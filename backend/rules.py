"""核心业务规则(PRD v5 §六 业务计算规则)。

单一定义、处处复用:API 计算、种子生成、单元测试共用同一套公式。
"""

from decimal import ROUND_HALF_UP, Decimal

# 保险:保额 1500 元/亩,总保费 = 保额 × 5%,农户自缴 = 总保费 × 20%(政府补贴 80%)
INSURED_AMOUNT_PER_MU = Decimal("1500")
PREMIUM_RATE = Decimal("0.05")
FARMER_PREMIUM_SHARE = Decimal("0.20")

# 贷款:建议额度 = 面积 × 800 元/亩(系统只出建议,银行自行决定)
LOAN_PER_MU = Decimal("800")

# 分红:平台引流订单按约定比例分给农户(试点默认 5%,运营可调)
DEFAULT_DIVIDEND_RATE = Decimal("0.05")

TWO_PLACES = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def insurance_quote(
    area_mu: float,
    per_mu: float = float(INSURED_AMOUNT_PER_MU),
    premium_rate: float = float(PREMIUM_RATE),
    farmer_share: float = float(FARMER_PREMIUM_SHARE),
) -> dict[str, float]:
    """按种植面积计算保额与保费;费率可由保险产品配置覆盖。"""
    area = Decimal(str(area_mu))
    insured_amount = _money(area * Decimal(str(per_mu)))
    total_premium = _money(insured_amount * Decimal(str(premium_rate)))
    farmer_premium = _money(total_premium * Decimal(str(farmer_share)))
    return {
        "insured_amount": float(insured_amount),
        "total_premium": float(total_premium),
        "farmer_premium": float(farmer_premium),
        "government_subsidy": float(_money(total_premium - farmer_premium)),
    }


def claim_amount(insured_amount: float, disaster_rate: float) -> float:
    """赔付金额 = 保额 × 受灾比例(管理员录入)。"""
    if not 0 <= disaster_rate <= 1:
        raise ValueError("disaster_rate 必须在 0 到 1 之间")
    return float(_money(Decimal(str(insured_amount)) * Decimal(str(disaster_rate))))


def loan_suggestion(area_mu: float) -> float:
    """建议额度 = 面积 × 800 元/亩。"""
    return float(_money(Decimal(str(area_mu)) * LOAN_PER_MU))


def risk_level(certified: bool, has_active_insurance: bool, profile_complete: bool = True) -> str:
    """风险评级:认证+有保险=LOW;无保险=MEDIUM;信息不全=HIGH。"""
    if not profile_complete:
        return "HIGH"
    if certified and has_active_insurance:
        return "LOW"
    return "MEDIUM"


def dividend_amount(base_amount: float, rate: float = float(DEFAULT_DIVIDEND_RATE)) -> float:
    """分红金额 = 订单基数 × 约定比例。"""
    return float(_money(Decimal(str(base_amount)) * Decimal(str(rate))))
