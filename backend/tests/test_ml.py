"""算法模型模块单元测试:解析器 / 特征 / 评分换算 / 推理降级。

不依赖数据库;涉及真实模型文件与种子文件的用例自动跳过。
"""

from __future__ import annotations

import os

import pytest

from backend.ml.features import (
    CREDIT_FEATURES,
    YIELD_FEATURES,
    farmer_credit_features,
    plot_yield_features,
    plot_yield_label,
)
from backend.ml.inference import credit_score, yield_predict
from backend.ml.scorecard import probability_from_score, risk_band, score_from_probability
from backend.ml.seed_loader import load_seed_sql

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED_PATH = os.path.join(REPO_ROOT, "danqiu_rice_seed.sql")

_SAMPLE_SQL = """
CREATE TABLE t (id INT, name VARCHAR(20), val DECIMAL(10,2), note TEXT);
INSERT INTO `farm_record`
  (`id`, `plot_id`, `record_type`, `record_date`, `output_jin`, `status`, `material_name`)
VALUES
(1, 10, 'HARVEST', '2025-05-01', 1200.50, 'VERIFIED', NULL),
(2, 11, 'SOWING', '2025-03-01', NULL, 'SUBMITTED', '复合肥'),
(3, 12, 'QUALITY_TEST', '2025-06-01', 950, 'VERIFIED', '含''引号'';分号');
"""


class TestSeedLoader:
    def test_parse_sample(self):
        tables = load_seed_sql(_write_sample())
        assert set(tables) == {"farm_record"}
        rows = tables["farm_record"]
        assert len(rows) == 3
        assert rows[0]["id"] == 1
        assert rows[0]["output_jin"] == 1200.5
        assert rows[0]["material_name"] is None
        assert rows[1]["material_name"] == "复合肥"
        assert rows[2]["output_jin"] == 950
        assert rows[2]["material_name"] == "含'引号';分号"

    def test_real_seed_counts(self):
        if not os.path.exists(SEED_PATH):
            pytest.skip("种子文件不存在")
        tables = load_seed_sql(SEED_PATH)
        assert len(tables["farmer_profile"]) >= 100
        assert len(tables["farm_record"]) >= 500


class TestFeatures:
    def test_farmer_credit_features(self):
        farmer = {
            "id": 1, "certification_status": "CERTIFIED",
            "address": "丹邱村", "id_card_masked": "4401***",
        }
        plots = [
            {"id": 1, "farmer_id": 1, "area_mu": 5, "status": "ACTIVE", "variety": "象牙香占"},
            {"id": 2, "farmer_id": 1, "area_mu": 3, "status": "ACTIVE", "variety": "象牙香占"},
        ]
        records = [
            {"plot_id": 1, "record_type": "HARVEST", "record_date": "2025-05-01",
             "material_amount": 10, "output_jin": 5000, "status": "VERIFIED"},
            {"plot_id": 1, "record_type": "SOWING", "record_date": "2025-03-01",
             "material_amount": 5, "output_jin": None, "status": "NEEDS_CORRECTION"},
            {"plot_id": 2, "record_type": "HARVEST", "record_date": "2025-05-10",
             "material_amount": 8, "output_jin": 2400, "status": "VERIFIED"},
        ]
        policies = [{"farmer_id": 1, "status": "ACTIVE"}]
        feats = farmer_credit_features(farmer, plots, records, policies)
        assert feats["certified"] == 1
        assert feats["has_insurance"] == 1
        assert feats["plot_count"] == 2
        assert feats["total_area_mu"] == 8
        assert feats["record_count"] == 3
        assert feats["correction_count"] == 1
        assert set(feats) == set(CREDIT_FEATURES)
        # 亩产:5000/5=1000, 2400/3=800 → 均值 900
        assert feats["avg_output_per_mu"] == 900

    def test_plot_yield_features_and_label(self):
        plot = {"id": 1, "farmer_id": 1, "area_mu": 4, "status": "ACTIVE", "variety": "象牙香占"}
        records = [
            {"plot_id": 1, "record_type": "HARVEST", "record_date": "2025-05-01",
             "material_amount": 10, "output_jin": 4000, "status": "VERIFIED"},
            {"plot_id": 1, "record_type": "FERTILIZING", "record_date": "2025-04-01",
             "material_amount": 20, "output_jin": None, "status": "VERIFIED"},
        ]
        feats = plot_yield_features(plot, records, {"certification_status": "PENDING"})
        assert feats["n_harvest"] == 1
        assert feats["n_fertilizing"] == 1
        assert feats["material_total"] == 30
        assert feats["variety"] == 2
        assert set(feats) == set(YIELD_FEATURES)
        assert plot_yield_label(records, 4) == 1000.0
        assert plot_yield_label([], 4) is None


class TestScorecard:
    def test_score_monotonic(self):
        assert score_from_probability(0.1) > score_from_probability(0.5)
        assert score_from_probability(0.5) > score_from_probability(0.9)
        assert 300 <= score_from_probability(0.999) <= 900

    def test_risk_band(self):
        assert risk_band(400) == "HIGH"
        assert risk_band(500) == "MEDIUM"
        assert risk_band(650) == "LOW"

    def test_score_known_value(self):
        # odds=1 (p=0.5) → score = base 600
        assert score_from_probability(0.5) == 600

    def test_probability_from_score(self):
        assert probability_from_score(600) == pytest.approx(0.5)
        assert probability_from_score(700) == pytest.approx(0.2, abs=0.001)
        assert probability_from_score(480) > probability_from_score(550)


class TestInferenceFallback:
    def test_credit_rule_fallback(self, monkeypatch):
        monkeypatch.setattr("backend.ml.inference._load_credit_artifact", lambda: None)
        result = credit_score({"certified": 1.0, "has_insurance": 1.0, "profile_complete": 1.0})
        assert result["model"] == "rule-fallback"
        assert result["score"] == 700
        assert result["default_probability"] == pytest.approx(0.2, abs=0.001)
        assert result["default_probability_source"] == "score-implied-estimate"
        assert result["risk_level"] == "LOW"

    def test_yield_fallback(self, monkeypatch):
        monkeypatch.setattr("backend.ml.inference._load_yield_artifact", lambda: None)
        result = yield_predict({name: 0.0 for name in YIELD_FEATURES})
        assert result["model"] == "rule-fallback"
        assert result["predicted_per_mu"] is None

    def test_credit_low_signal_gate(self):
        """真实评分卡(种子标签为随机生成,AUC≈0.55)应被质量门禁拦截并降级。"""
        model_path = os.path.join(REPO_ROOT, "backend/ml/models/credit_scorecard.joblib")
        if not os.path.exists(model_path):
            pytest.skip("评分卡模型文件不存在")
        result = credit_score({"certified": 1.0, "has_insurance": 1.0, "profile_complete": 1.0})
        assert result["model_status"]["enabled"] is False
        assert result["model"] == "rule-fallback"
        assert "信号不足" in result["note"]

    def test_yield_model_enabled(self):
        """真实产量模型(R²≈0.50)应通过门禁并输出预测值。"""
        model_path = os.path.join(REPO_ROOT, "backend/ml/models/yield_model.joblib")
        if not os.path.exists(model_path):
            pytest.skip("产量模型文件不存在")
        feats = {name: 0.0 for name in YIELD_FEATURES}
        feats.update({"area_mu": 6.0, "n_fertilizing": 3.0, "n_records": 10.0})
        result = yield_predict(feats)
        assert result["model_status"]["enabled"] is True
        assert result["predicted_per_mu"] is not None


def _write_sample() -> str:
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as fh:
        fh.write(_SAMPLE_SQL)
        return fh.name
