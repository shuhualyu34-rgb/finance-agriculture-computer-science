"""模型推理:加载 joblib 模型打分;模型缺失或信号不足时降级为规则计算。

质量门禁:评分卡要求 AUC >= 0.60、产量模型要求 R² >= 0.20,未达标自动降级,
避免在种子数据(审批标签为随机生成)上输出误导性分数。
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from backend.ml.features import CREDIT_FEATURES, YIELD_FEATURES
from backend.ml.scorecard import probability_from_score, risk_band, score_from_probability

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
CREDIT_MODEL_PATH = os.path.join(MODELS_DIR, "credit_scorecard.joblib")
YIELD_MODEL_PATH = os.path.join(MODELS_DIR, "yield_model.joblib")

CREDIT_AUC_THRESHOLD = 0.60
YIELD_R2_THRESHOLD = 0.20


@lru_cache(maxsize=1)
def _load_credit_artifact() -> dict[str, Any] | None:
    if not os.path.exists(CREDIT_MODEL_PATH):
        return None
    try:
        import joblib

        return joblib.load(CREDIT_MODEL_PATH)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_yield_artifact() -> dict[str, Any] | None:
    if not os.path.exists(YIELD_MODEL_PATH):
        return None
    try:
        import joblib

        return joblib.load(YIELD_MODEL_PATH)
    except Exception:
        return None


def credit_score(features: dict[str, float]) -> dict[str, Any]:
    """信用评分:返回评分、违约概率、风险档与模型标识。

    模型缺失或 AUC 低于阈值时,降级为规则评分(与 rules.risk_level 同口径)。
    """
    artifact = _load_credit_artifact()
    auc = _credit_auc(artifact)
    if artifact is None or auc is None or auc < CREDIT_AUC_THRESHOLD:
        score = _rule_fallback_score(features)
        result: dict[str, Any] = {
            "score": score,
            "default_probability": round(probability_from_score(score), 4),
            "default_probability_source": "score-implied-estimate",
            "risk_level": risk_band(score),
            "model": "rule-fallback",
            "model_status": {
                "loaded": artifact is not None,
                "auc": auc,
                "enabled": False,
            },
        }
        if artifact is not None:
            result["note"] = (
                f"评分卡信号不足(AUC {auc:.3f} < {CREDIT_AUC_THRESHOLD:.2f}),"
                "已降级为规则评分;接入真实信贷数据重训后可启用"
            )
        else:
            result["note"] = "未加载评分卡模型,已降级为规则评分"
        return result
    try:
        import numpy as np

        x = np.array([[features.get(name, 0.0) for name in CREDIT_FEATURES]], dtype=float)
        proba = float(artifact["model"].predict_proba(x)[0, 1])
    except Exception:
        proba = 0.5
    score = score_from_probability(proba)
    return {
        "score": score,
        "default_probability": round(proba, 4),
        "risk_level": risk_band(score),
        "model": artifact.get("version", "v1"),
        "model_status": {"loaded": True, "auc": auc, "enabled": True},
        "metrics": artifact.get("metrics"),
    }


def yield_predict(features: dict[str, float]) -> dict[str, Any]:
    """产量预测(亩产,斤/亩)。模型缺失或 R² 不足时降级(由接口用历史均值兜底)。"""
    artifact = _load_yield_artifact()
    r2 = _yield_r2(artifact)
    if artifact is None or r2 is None or r2 < YIELD_R2_THRESHOLD:
        return {
            "predicted_per_mu": None,
            "model": "rule-fallback",
            "model_status": {
                "loaded": artifact is not None,
                "r2": r2,
                "enabled": False,
            },
            "note": "产量模型信号不足或未加载,请训练模型或使用历史均值",
        }
    try:
        import numpy as np

        x = np.array([[features.get(name, 0.0) for name in YIELD_FEATURES]], dtype=float)
        predicted = float(artifact["model"].predict(x)[0])
    except Exception:
        predicted = None
    return {
        "predicted_per_mu": round(predicted, 2) if predicted is not None else None,
        "model": artifact.get("version", "v1"),
        "model_name": artifact.get("model_name"),
        "model_status": {"loaded": True, "r2": r2, "enabled": True},
        "metrics": artifact.get("metrics", {}).get("selected"),
    }


def model_info() -> dict[str, Any]:
    """模型文件状态(用于接口/文档展示)。"""
    credit = _load_credit_artifact()
    yield_ = _load_yield_artifact()
    return {
        "credit_scorecard": {
            "loaded": credit is not None,
            "version": credit.get("version") if credit else None,
            "auc": _credit_auc(credit),
            "enabled": _credit_auc(credit) is not None and _credit_auc(credit) >= CREDIT_AUC_THRESHOLD,
            "metrics": credit.get("metrics") if credit else None,
        },
        "yield_model": {
            "loaded": yield_ is not None,
            "version": yield_.get("version") if yield_ else None,
            "r2": _yield_r2(yield_),
            "enabled": _yield_r2(yield_) is not None and _yield_r2(yield_) >= YIELD_R2_THRESHOLD,
            "metrics": yield_.get("metrics") if yield_ else None,
        },
    }


def _credit_auc(artifact: dict[str, Any] | None) -> float | None:
    if not artifact:
        return None
    metrics = artifact.get("metrics") or {}
    return metrics.get("test_auc") or metrics.get("cv_auc")


def _yield_r2(artifact: dict[str, Any] | None) -> float | None:
    if not artifact:
        return None
    metrics = artifact.get("metrics") or {}
    selected = metrics.get("selected") or {}
    return selected.get("r2") or metrics.get("random_forest", {}).get("r2")


def _rule_fallback_score(features: dict[str, float]) -> int:
    """无模型/信号不足时的规则评分:与 rules.risk_level 口径一致,映射为粗分。"""
    certified = features.get("certified", 0.0) >= 0.5
    has_insurance = features.get("has_insurance", 0.0) >= 0.5
    complete = features.get("profile_complete", 1.0) >= 0.5
    if not complete:
        return 380
    if certified and has_insurance:
        return 700
    if has_insurance:
        return 550
    return 480
