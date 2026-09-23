"""算法模型推理接口:信用评分卡(银行端)+ 产量预测(保险端)。

模型文件缺失时自动降级为规则计算,接口始终可用。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.auth import require_roles
from backend.db import query
from backend.ml.features import farmer_credit_features, plot_yield_features
from backend.ml.inference import credit_score, yield_predict

router = APIRouter(prefix="/api", tags=["ml"])

BankOnly = Depends(require_roles("BANK", "ADMIN"))
InsuranceOnly = Depends(require_roles("INSURANCE", "ADMIN"))


def _fetch_farmer(farmer_id: int) -> dict[str, Any]:
    row = query(
        """
        SELECT id, certification_status, address, id_card_masked
        FROM farmer_profile WHERE id = %s
        """,
        (farmer_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="农户不存在")
    return row[0]


def _fetch_farmer_credit_data(
    farmer_id: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    farmer = _fetch_farmer(farmer_id)
    plots = query(
        "SELECT id, farmer_id, area_mu, status, variety FROM farm_plot WHERE farmer_id = %s",
        (farmer_id,),
    )
    records = query(
        """
        SELECT r.plot_id, r.record_type, r.record_date, r.material_amount,
               r.output_jin, r.status
        FROM farm_record r
        JOIN farm_plot p ON p.id = r.plot_id
        WHERE p.farmer_id = %s
        """,
        (farmer_id,),
    )
    policies = query(
        "SELECT farmer_id, status FROM insurance_policy WHERE farmer_id = %s",
        (farmer_id,),
    )
    return farmer, plots, records, policies


@router.get("/bank/credit-score/{farmer_id}", dependencies=[BankOnly])
def bank_credit_score(farmer_id: int) -> dict[str, Any]:
    """银行端:农户信用评分(评分卡 / 降级规则)。"""
    farmer, plots, records, policies = _fetch_farmer_credit_data(farmer_id)
    features = farmer_credit_features(farmer, plots, records, policies)
    result = credit_score(features)
    result["farmer_id"] = farmer_id
    result["features"] = features
    return result


@router.get("/bank/credit-scores", dependencies=[BankOnly])
def bank_credit_scores(farmer_ids: str = Query(default="")) -> dict[str, Any]:
    """银行端:批量信用评分(贷款列表用,单请求返回,避免前端逐户调用的 N+1)。"""
    ids = [int(p) for p in (s.strip() for s in farmer_ids.split(",")) if p.isdigit()]
    ids = list(dict.fromkeys(ids))[:50]
    scores: dict[str, Any] = {}
    for fid in ids:
        try:
            farmer, plots, records, policies = _fetch_farmer_credit_data(fid)
        except HTTPException:
            continue  # 农户不存在时跳过,不影响其他农户
        result = credit_score(farmer_credit_features(farmer, plots, records, policies))
        scores[str(fid)] = {
            "score": result.get("score"),
            "risk_level": result.get("risk_level"),
            "default_probability": result.get("default_probability"),
            "model_enabled": bool((result.get("model_status") or {}).get("enabled")),
        }
    return {"scores": scores}


@router.get("/insurance/yield-prediction/{plot_id}", dependencies=[InsuranceOnly])
def insurance_yield_prediction(plot_id: int) -> dict[str, Any]:
    """保险端:地块产量预测(斤/亩),含与历史实际亩产的偏差(损失评估参考)。"""
    plot = query(
        "SELECT id, farmer_id, area_mu, variety, status FROM farm_plot WHERE id = %s",
        (plot_id,),
    )
    if not plot:
        raise HTTPException(status_code=404, detail="地块不存在")
    plot = plot[0]
    farmer = query(
        "SELECT id, certification_status FROM farmer_profile WHERE id = %s",
        (plot["farmer_id"],),
    )
    records = query(
        """
        SELECT record_type, record_date, material_amount, output_jin, status
        FROM farm_record WHERE plot_id = %s
        """,
        (plot_id,),
    )
    features = plot_yield_features(plot, records, farmer[0] if farmer else None)
    result = yield_predict(features)

    # 历史实际亩产(用于偏差与损失评估)
    actual_list = [
        float(r["output_jin"]) / float(plot["area_mu"])
        for r in records
        if r.get("output_jin") and r.get("record_type") in ("HARVEST", "QUALITY_TEST")
        and float(plot["area_mu"]) > 0
    ]
    actual = round(sum(actual_list) / len(actual_list), 2) if actual_list else None
    result["plot_id"] = plot_id
    result["area_mu"] = float(plot["area_mu"])
    result["actual_per_mu"] = actual
    result["predicted_output_jin"] = (
        round(result["predicted_per_mu"] * float(plot["area_mu"]), 2)
        if result.get("predicted_per_mu") is not None
        else None
    )
    result["deviation_pct"] = (
        round((result["predicted_per_mu"] - actual) / actual * 100, 2)
        if result.get("predicted_per_mu") is not None and actual
        else None
    )
    result["features"] = features
    return result
