"""纯单元测试:不依赖数据库,验证业务规则(PRD v5 §六)。"""

from decimal import Decimal

import pytest

from backend.db import normalize
from backend.rules import (
    claim_amount,
    dividend_amount,
    insurance_quote,
    loan_suggestion,
    product_quote,
    risk_level,
    weather_index_assessment,
)


def test_normalize_decimal():
    assert normalize(Decimal("12.30")) == 12.3
    assert normalize(Decimal("0")) == 0.0


def test_normalize_passthrough():
    assert normalize(3) == 3
    assert normalize("文本") == "文本"
    assert normalize(None) is None


class TestInsuranceQuote:
    """保额 = 面积 × 1500;总保费 = 保额 × 5%;农户自缴 = 总保费 × 20%。"""

    def test_ten_mu(self):
        q = insurance_quote(10)
        assert q["insured_amount"] == 15000
        assert q["total_premium"] == 750
        assert q["farmer_premium"] == 150
        assert q["government_subsidy"] == 600

    def test_fractional_mu(self):
        q = insurance_quote(2.5)
        assert q["insured_amount"] == 3750
        assert q["farmer_premium"] == 37.5

    def test_product_rate_override(self):
        q = insurance_quote(10, per_mu=2000, premium_rate=0.04, farmer_share=0.1)
        assert q["insured_amount"] == 20000
        assert q["total_premium"] == 800
        assert q["farmer_premium"] == 80


class TestClaim:
    def test_payout(self):
        assert claim_amount(15000, 0.3) == 4500

    def test_rate_bounds(self):
        with pytest.raises(ValueError):
            claim_amount(15000, 1.5)
        with pytest.raises(ValueError):
            claim_amount(15000, -0.1)


def test_product_matrix_quote():
    q = product_quote(10, {
        "product_code": "WEATHER-001",
        "product_type": "WEATHER_INDEX",
        "insured_amount_per_mu": 800,
        "premium_rate": 0.045,
        "government_subsidy_rate": 0.40,
    })
    assert q["insured_amount"] == 8000
    assert q["total_premium"] == 360
    assert q["farmer_premium"] == 216
    assert q["product_type"] == "WEATHER_INDEX"


def test_weather_index_assessment():
    quiet = weather_index_assessment(8000, {"wind_speed_kmh": 80, "rainfall_mm": 120}, 50, 80)
    assert quiet["triggered"] is False
    storm = weather_index_assessment(8000, {"wind_speed_kmh": 80, "rainfall_mm": 120}, 100, 80)
    assert storm["triggered"] is True
    assert storm["claim_amount"] > 0
    assert storm["claim_amount"] <= 8000


class TestLoan:
    def test_suggestion(self):
        assert loan_suggestion(12.5) == 10000

    def test_risk_levels(self):
        assert risk_level(True, True) == "LOW"
        assert risk_level(False, True) == "MEDIUM"
        assert risk_level(True, False) == "MEDIUM"
        assert risk_level(False, False) == "MEDIUM"
        assert risk_level(True, True, profile_complete=False) == "HIGH"


class TestDividend:
    def test_default_rate(self):
        assert dividend_amount(1000) == 50

    def test_custom_rate(self):
        assert dividend_amount(1000, rate=0.08) == 80
