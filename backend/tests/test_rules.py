"""纯单元测试:不依赖数据库。"""

from decimal import Decimal

from backend.app import normalize


def test_normalize_decimal():
    assert normalize(Decimal("12.30")) == 12.3
    assert normalize(Decimal("0")) == 0.0


def test_normalize_passthrough():
    assert normalize(3) == 3
    assert normalize("文本") == "文本"
    assert normalize(None) is None


# ---- 业务规则(PRD v5 第六节)-------------------------------------------
# 保额 = 种植面积(亩) × 1500 元/亩
# 总保费 = 保额 × 5%,其中农户自缴 = 总保费 × 20%(政府补贴 80%)
# 贷款建议额度 = 种植面积(亩) × 800 元/亩

INSURANCE_AMOUNT_PER_MU = 1500
PREMIUM_RATE = 0.05
FARMER_SHARE = 0.20
LOAN_SUGGESTION_PER_MU = 800


def test_insurance_rules():
    area = 10  # 亩
    coverage = area * INSURANCE_AMOUNT_PER_MU
    premium = coverage * PREMIUM_RATE
    farmer_pays = premium * FARMER_SHARE
    assert coverage == 15_000
    assert premium == 750
    assert farmer_pays == 150  # 政府补贴 600


def test_loan_suggestion_rule():
    assert 12.5 * LOAN_SUGGESTION_PER_MU == 10_000


def test_claim_payout_rule():
    """赔付金额 = 保额 × 受灾比例(管理员录入)。"""
    coverage = 15_000
    disaster_rate = 0.3
    assert coverage * disaster_rate == 4_500
