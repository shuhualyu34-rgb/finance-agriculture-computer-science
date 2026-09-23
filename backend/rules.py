"""核心业务规则(PRD v5 §六 业务计算规则)。

单一定义、处处复用:API 计算、种子生成、单元测试共用同一套公式。
"""

import json
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


def product_quote(area_mu: float, product: dict) -> dict[str, float | str]:
    """按保险产品配置试算，兼容原有基础种植保险公式。"""
    quote = insurance_quote(
        area_mu,
        per_mu=float(product["insured_amount_per_mu"]),
        premium_rate=float(product["premium_rate"]),
        farmer_share=1 - float(product["government_subsidy_rate"]),
    )
    quote["product_code"] = product.get("product_code", "COST-001")
    quote["product_type"] = product.get("product_type", "COST")
    return quote


def weather_index_assessment(
    insured_amount: float,
    trigger_config: dict | str | None,
    wind_speed_kmh: float = 0,
    rainfall_mm: float = 0,
) -> dict[str, float | bool | str]:
    """演示级气象指数定损：达到任一阈值即触发，赔付比例封顶 100%。"""
    config = json.loads(trigger_config) if isinstance(trigger_config, str) else (trigger_config or {})
    wind_threshold = float(config.get("wind_speed_kmh", 80))
    rain_threshold = float(config.get("rainfall_mm", 120))
    wind_ratio = float(wind_speed_kmh) / wind_threshold if wind_threshold else 0
    rain_ratio = float(rainfall_mm) / rain_threshold if rain_threshold else 0
    trigger_ratio = max(wind_ratio, rain_ratio)
    triggered = trigger_ratio >= 1
    loss_rate = min(1.0, max(0.0, (trigger_ratio - 0.8) / 0.8)) if triggered else 0.0
    return {
        "triggered": triggered,
        "loss_rate": round(loss_rate, 4),
        "claim_amount": claim_amount(insured_amount, loss_rate),
        "wind_threshold_kmh": wind_threshold,
        "rainfall_threshold_mm": rain_threshold,
        "wind_speed_kmh": float(wind_speed_kmh),
        "rainfall_mm": float(rainfall_mm),
        "source": "DEMO_INPUT",
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
