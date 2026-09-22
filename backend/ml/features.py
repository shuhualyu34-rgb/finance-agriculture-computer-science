"""特征工程:信用评分卡 + 产量预测 的特征定义。

训练(离线,解析种子 SQL)与推理(在线,查数据库)复用同一套特征逻辑,
保证线上打分与训练分布一致。所有特征均为数值型,便于直接进入 sklearn。
"""

from __future__ import annotations

import statistics
from datetime import date, datetime
from typing import Any

RECORD_TYPES = ["SOWING", "FERTILIZING", "PESTICIDE", "IRRIGATION", "HARVEST", "QUALITY_TEST"]

CREDIT_FEATURES = [
    "certified",            # 是否品牌认证通过
    "has_insurance",        # 是否有在保/在途保单
    "profile_complete",     # 档案信息是否完整(地址+脱敏身份证)
    "plot_count",           # 地块数量
    "total_area_mu",        # 总面积(亩)
    "record_count",         # 农事记录总数
    "type_coverage",        # 覆盖的农事类型数(0-6)
    "recent_record_count",  # 近 90 天农事记录数
    "record_span_days",     # 农事记录时间跨度(天)
    "avg_output_per_mu",    # 历史平均亩产(斤/亩)
    "output_cv",            # 亩产变异系数(0 表示样本不足)
    "correction_count",     # 待整改记录数
]

YIELD_FEATURES = [
    "area_mu",              # 地块面积
    "certified",            # 农户认证状态
    "n_sowing",             # 播种次数
    "n_fertilizing",        # 施肥次数
    "n_pesticide",          # 打药次数
    "n_irrigation",         # 灌溉次数
    "n_harvest",            # 收割次数
    "n_quality_test",       # 质检次数
    "n_records",            # 记录总数
    "material_total",       # 投入品总量
    "span_days",            # 记录时间跨度
    "correction_count",     # 待整改记录数
    "variety",              # 品种编码
]

# 品种有限且固定(种子数据),按枚举编码;未知品种归 0
VARIETY_MAP = {
    "增科新选丝苗1号": 1,
    "增科丝苗1号": 1,
    "象牙香占": 2,
    "粤禾丝苗": 3,
    "美香占2号": 4,
    "南晶香占": 5,
}

_YIELD_RECORD_TYPES = {"HARVEST", "QUALITY_TEST"}


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def farmer_credit_features(
    farmer: dict[str, Any],
    plots: list[dict[str, Any]],
    records: list[dict[str, Any]],
    policies: list[dict[str, Any]],
) -> dict[str, float]:
    """单农户信用评分特征。records 为该农户全部地块的农事记录。"""
    active_plots = [p for p in plots if str(p.get("status", "ACTIVE")) == "ACTIVE"]
    area_by_plot: dict[int, float] = {}
    for p in active_plots:
        try:
            area_by_plot[int(p["id"])] = _to_float(p.get("area_mu"))
        except (TypeError, ValueError):
            continue

    record_dates: list[date] = []
    per_mu_outputs: list[float] = []
    correction = 0
    recent = 0
    record_types: set[str] = set()
    for r in records:
        rtype = str(r.get("record_type", ""))
        if rtype:
            record_types.add(rtype)
        if str(r.get("status", "")) == "NEEDS_CORRECTION":
            correction += 1
        d = _to_date(r.get("record_date"))
        if d:
            record_dates.append(d)
        output = _to_float(r.get("output_jin"))
        if output > 0 and rtype in _YIELD_RECORD_TYPES:
            area = area_by_plot.get(_plot_id_of(r))
            if area and area > 0:
                per_mu_outputs.append(output / area)

    # 近 90 天:以数据集中最晚记录日期为基准
    if record_dates:
        anchor = max(record_dates)
        recent = sum(1 for d in record_dates if (anchor - d).days <= 90)

    avg_output = statistics.mean(per_mu_outputs) if per_mu_outputs else 0.0
    cv = 0.0
    if len(per_mu_outputs) >= 2 and avg_output > 0:
        cv = statistics.pstdev(per_mu_outputs) / avg_output

    has_insurance = any(
        str(p.get("status", "")) in ("APPLIED", "ACTIVE") for p in policies
    )
    profile_complete = (
        farmer.get("address") is not None
        and farmer.get("id_card_masked") is not None
        and str(farmer.get("address", "")).strip() != ""
    )
    span = (
        (max(record_dates) - min(record_dates)).days
        if len(record_dates) >= 2
        else 0
    )
    return {
        "certified": 1.0 if str(farmer.get("certification_status", "")) == "CERTIFIED" else 0.0,
        "has_insurance": 1.0 if has_insurance else 0.0,
        "profile_complete": 1.0 if profile_complete else 0.0,
        "plot_count": float(len(active_plots)),
        "total_area_mu": float(sum(area_by_plot.values())),
        "record_count": float(len(records)),
        "type_coverage": float(len(record_types)),
        "recent_record_count": float(recent),
        "record_span_days": float(span),
        "avg_output_per_mu": round(avg_output, 2),
        "output_cv": round(cv, 4),
        "correction_count": float(correction),
    }


def plot_yield_features(
    plot: dict[str, Any],
    records: list[dict[str, Any]],
    farmer: dict[str, Any] | None = None,
) -> dict[str, float]:
    """单地块产量预测特征。records 为该地块全部农事记录。"""
    counts = {t: 0 for t in RECORD_TYPES}
    material_total = 0.0
    correction = 0
    dates: list[date] = []
    for r in records:
        rtype = str(r.get("record_type", ""))
        if rtype in counts:
            counts[rtype] += 1
        material_total += _to_float(r.get("material_amount"))
        if str(r.get("status", "")) == "NEEDS_CORRECTION":
            correction += 1
        d = _to_date(r.get("record_date"))
        if d:
            dates.append(d)
    span = (max(dates) - min(dates)).days if len(dates) >= 2 else 0
    certified = (
        str(farmer.get("certification_status", "")) == "CERTIFIED"
        if farmer
        else False
    )
    variety = VARIETY_MAP.get(str(plot.get("variety", "")), 0)
    return {
        "area_mu": _to_float(plot.get("area_mu")),
        "certified": 1.0 if certified else 0.0,
        "n_sowing": float(counts["SOWING"]),
        "n_fertilizing": float(counts["FERTILIZING"]),
        "n_pesticide": float(counts["PESTICIDE"]),
        "n_irrigation": float(counts["IRRIGATION"]),
        "n_harvest": float(counts["HARVEST"]),
        "n_quality_test": float(counts["QUALITY_TEST"]),
        "n_records": float(len(records)),
        "material_total": round(material_total, 2),
        "span_days": float(span),
        "correction_count": float(correction),
        "variety": float(variety),
    }


def plot_yield_label(records: list[dict[str, Any]], area_mu: float) -> float | None:
    """地块产量标签:有产量记录的亩产均值(斤/亩);无产量记录返回 None。"""
    outputs: list[float] = []
    for r in records:
        rtype = str(r.get("record_type", ""))
        output = _to_float(r.get("output_jin"))
        if rtype in _YIELD_RECORD_TYPES and output > 0:
            outputs.append(output)
    if not outputs or area_mu <= 0:
        return None
    return round(sum(outputs) / len(outputs) / area_mu, 2)


def _plot_id_of(record: dict[str, Any]) -> int | None:
    try:
        return int(record["plot_id"])
    except (TypeError, ValueError, KeyError):
        return None
