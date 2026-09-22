"""训练数据集构建:从解析后的种子表生成 (特征, 标签)。"""

from __future__ import annotations

from typing import Any

from backend.ml.features import (
    farmer_credit_features,
    plot_yield_features,
    plot_yield_label,
)


def build_credit_dataset(tables: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, float]], list[int]]:
    """信用评分训练集。

    标签 = 农户最近一笔贷款申请的银行审批结果(APPROVED=1 / REJECTED=0);
    PENDING 或无贷款记录的农户不进入训练集(线上推理时仍可打分)。
    """
    farmers = tables.get("farmer_profile", [])
    plots = tables.get("farm_plot", [])
    records = tables.get("farm_record", [])
    policies = tables.get("insurance_policy", [])
    loans = tables.get("loan_application", [])

    plots_by_farmer: dict[int, list[dict[str, Any]]] = {}
    for p in plots:
        plots_by_farmer.setdefault(int(p["farmer_id"]), []).append(p)
    records_by_farmer: dict[int, list[dict[str, Any]]] = {}
    plot_to_farmer: dict[int, int] = {}
    for p in plots:
        plot_to_farmer[int(p["id"])] = int(p["farmer_id"])
    for r in records:
        fid = plot_to_farmer.get(int(r["plot_id"]))
        if fid is not None:
            records_by_farmer.setdefault(fid, []).append(r)
    policies_by_farmer: dict[int, list[dict[str, Any]]] = {}
    for po in policies:
        policies_by_farmer.setdefault(int(po["farmer_id"]), []).append(po)

    # 每农户最近一笔贷款
    latest_loan: dict[int, dict[str, Any]] = {}
    for loan in loans:
        fid = int(loan["farmer_id"])
        if loan.get("bank_result") in ("APPROVED", "REJECTED"):
            cur = latest_loan.get(fid)
            if cur is None or _loan_order(loan) >= _loan_order(cur):
                latest_loan[fid] = loan

    X: list[dict[str, float]] = []
    y: list[int] = []
    for farmer in farmers:
        fid = int(farmer["id"])
        loan = latest_loan.get(fid)
        if loan is None:
            continue
        feats = farmer_credit_features(
            farmer,
            plots_by_farmer.get(fid, []),
            records_by_farmer.get(fid, []),
            policies_by_farmer.get(fid, []),
        )
        X.append(feats)
        y.append(1 if loan["bank_result"] == "APPROVED" else 0)
    return X, y


def build_yield_dataset(tables: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, float]], list[float]]:
    """产量预测训练集:地块级样本,标签 = 亩产(斤/亩)。

    只有存在产量记录(HARVEST/QUALITY_TEST 且 output_jin>0)的地块进入训练集。
    """
    farmers = tables.get("farmer_profile", [])
    plots = tables.get("farm_plot", [])
    records = tables.get("farm_record", [])
    farmer_by_id = {int(f["id"]): f for f in farmers}

    records_by_plot: dict[int, list[dict[str, Any]]] = {}
    for r in records:
        records_by_plot.setdefault(int(r["plot_id"]), []).append(r)

    X: list[dict[str, float]] = []
    y: list[float] = []
    for plot in plots:
        pid = int(plot["id"])
        recs = records_by_plot.get(pid, [])
        area = float(plot.get("area_mu") or 0)
        label = plot_yield_label(recs, area)
        if label is None:
            continue
        farmer = farmer_by_id.get(int(plot["farmer_id"]))
        feats = plot_yield_features(plot, recs, farmer)
        X.append(feats)
        y.append(label)
    return X, y


def _loan_order(loan: dict[str, Any]) -> int:
    try:
        return int(loan.get("id") or 0)
    except (TypeError, ValueError):
        return 0
