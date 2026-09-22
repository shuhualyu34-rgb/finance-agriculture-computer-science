"""政府监管大屏(PRD v5 §4.6):数字卡片、地块地图、最新业务动态。

大屏用于展厅公开展示,接口保持公开(与既有 /api/government/summary 一致)。
"""

import json
from contextlib import contextmanager
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
import pymysql

from backend.auth import require_roles
from backend.config import DB_CONFIG
from backend.db import query

router = APIRouter(prefix="/api/government", tags=["government"])


government_user = Depends(require_roles("GOVERNMENT", "ADMIN"))


@router.get("/workbench", dependencies=[government_user])
def workbench() -> dict[str, Any]:
    """政府工作台:监管卡片、异常预警、现场核验和周期报表。"""
    cards = query(
        """
        SELECT
          (SELECT COUNT(*) FROM farmer_profile) AS farmer_count,
          (SELECT COUNT(*) FROM farm_plot WHERE status = 'ACTIVE') AS active_plot_count,
          (SELECT COUNT(*) FROM field_inspection WHERE result IN ('WARNING','FAIL')) AS warning_count,
          (SELECT COUNT(*) FROM farm_record WHERE status = 'NEEDS_CORRECTION') AS correction_count,
          (SELECT COUNT(*) FROM regulatory_report WHERE status = 'DRAFT') AS draft_report_count,
          (SELECT COUNT(*) FROM farmer_certification WHERE status = 'PENDING') AS pending_cert_count
        """
    )[0]
    alerts = query(
        """
        SELECT fi.id, 'FIELD_INSPECTION' AS alert_type, fi.result AS level,
               fi.inspection_date AS occurred_at, p.plot_name, p.village,
               u.real_name AS owner_name, fi.difference_note AS detail,
               fi.rectification_required
        FROM field_inspection fi
        JOIN farm_plot p ON p.id = fi.plot_id
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE fi.result IN ('WARNING','FAIL')
        UNION ALL
        SELECT r.id, 'FARM_RECORD' AS alert_type, 'WARNING' AS level,
               r.record_date AS occurred_at, p.plot_name, p.village,
               u.real_name AS owner_name, r.description AS detail, 1 AS rectification_required
        FROM farm_record r
        JOIN farm_plot p ON p.id = r.plot_id
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE r.status = 'NEEDS_CORRECTION'
        ORDER BY occurred_at DESC LIMIT 30
        """
    )
    inspections = query(
        """
        SELECT fi.id, fi.plot_id, fi.inspection_date, fi.result,
               fi.difference_note, fi.rectification_required, fi.created_at,
               p.plot_name, p.village, u.real_name AS inspector_name
        FROM field_inspection fi
        JOIN farm_plot p ON p.id = fi.plot_id
        JOIN sys_user u ON u.id = fi.inspector_id
        ORDER BY fi.inspection_date DESC, fi.id DESC LIMIT 50
        """
    )
    reports = query(
        """
        SELECT r.id, r.report_type, r.report_period, r.content_json, r.status,
               r.confirmed_at, u.real_name AS confirmer_name, r.created_at
        FROM regulatory_report r
        LEFT JOIN sys_user u ON u.id = r.confirmed_by
        ORDER BY r.created_at DESC, r.id DESC LIMIT 30
        """
    )
    for report in reports:
        try:
            report["content"] = json.loads(report.pop("content_json"))
        except (TypeError, json.JSONDecodeError):
            report["content"] = {}
    return {"cards": cards, "alerts": alerts, "inspections": inspections, "reports": reports}


@router.get("/plots", dependencies=[government_user])
def inspection_plots() -> list[dict[str, Any]]:
    return query(
        """
        SELECT p.id, p.plot_name, p.village, p.plot_code, u.real_name AS farmer_name
        FROM farm_plot p
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE p.status = 'ACTIVE' ORDER BY p.plot_name
        """
    )


@router.post("/inspections", dependencies=[government_user])
def create_inspection(body: dict[str, Any] = Body(...), user: dict[str, Any] = Depends(require_roles("GOVERNMENT", "ADMIN"))) -> dict[str, Any]:
    required = ("plot_id", "inspection_date", "result")
    if any(body.get(key) in (None, "") for key in required):
        raise HTTPException(status_code=422, detail="地块、核验日期和核验结果不能为空")
    if body["result"] not in {"PASS", "WARNING", "FAIL"}:
        raise HTTPException(status_code=422, detail="核验结果不合法")
    with _transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO field_inspection
              (plot_id, inspector_id, inspection_date, result, difference_note, rectification_required)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (body["plot_id"], user["id"], body["inspection_date"], body["result"],
             body.get("difference_note") or None, bool(body.get("rectification_required"))),
        )
        return {"id": cursor.lastrowid, "result": body["result"]}


@router.put("/reports/{report_id}/confirm", dependencies=[government_user])
def confirm_report(report_id: int, user: dict[str, Any] = Depends(require_roles("GOVERNMENT", "ADMIN"))) -> dict[str, Any]:
    report = query("SELECT id, status FROM regulatory_report WHERE id = %s", (report_id,))
    if not report:
        raise HTTPException(status_code=404, detail="监管报表不存在")
    if report[0]["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail="只有草稿报表可以确认")
    with _transaction() as cursor:
        cursor.execute(
            "UPDATE regulatory_report SET status = 'CONFIRMED', confirmed_by = %s, confirmed_at = NOW() WHERE id = %s",
            (user["id"], report_id),
        )
    return {"id": report_id, "status": "CONFIRMED"}


@contextmanager
def _transaction():
    connection = pymysql.connect(**DB_CONFIG)
    try:
        connection.begin()
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.get("/dashboard")
def dashboard() -> dict[str, Any]:
    """大屏一次拉取:卡片指标 + 地块地图(GeoJSON 边界)+ 最新动态。"""
    cards = query(
        """
        SELECT
          (SELECT COUNT(*) FROM farmer_profile) AS total_farmers,
          (SELECT COUNT(*) FROM farmer_profile WHERE certification_status = 'CERTIFIED') AS certified_farmers,
          (SELECT COUNT(*) FROM loan_application) AS loan_applications,
          (SELECT COUNT(*) FROM loan_application WHERE bank_result = 'APPROVED') AS approved_loans,
          (SELECT COALESCE(SUM(suggested_amount), 0) FROM loan_application
             WHERE bank_result = 'APPROVED') AS approved_loan_amount,
          (SELECT COUNT(*) FROM insurance_policy) AS policy_count,
          (SELECT COUNT(*) FROM insurance_policy WHERE status = 'ACTIVE') AS active_policy_count,
          (SELECT COALESCE(SUM(insured_amount), 0) FROM insurance_policy) AS insured_amount_total,
          (SELECT COUNT(*) FROM insurance_claim) AS claim_count,
          (SELECT COALESCE(SUM(claim_amount), 0) FROM insurance_claim WHERE status = 'PAID') AS paid_claim_amount,
          (SELECT COUNT(DISTINCT consumer_user_id) FROM adoption_order) AS adoption_consumers,
          (SELECT COUNT(*) FROM adoption_order WHERE status IN ('PAID','ACTIVE')) AS adoption_count,
          (SELECT COUNT(*) FROM sales_order WHERE status <> 'CANCELLED') AS orders_count,
          (SELECT COALESCE(SUM(total_amount), 0) FROM sales_order
             WHERE source = 'PLATFORM' AND status <> 'CANCELLED') AS platform_sales_amount,
          (SELECT COALESCE(SUM(dividend_amount), 0) FROM farmer_dividend WHERE status <> 'SETTLED') AS pending_dividend,
          (SELECT COUNT(*) FROM farm_record) AS production_records,
          (SELECT COUNT(*) FROM field_inspection WHERE result IN ('WARNING','FAIL')) AS inspection_warnings
        """
    )[0]

    plots = query(
        """
        SELECT p.id, p.plot_name, p.village, p.area_mu, p.variety,
               p.longitude, p.latitude, p.boundary_json, p.status, p.open_for_adoption,
               (SELECT c.status FROM farmer_certification c
                 WHERE c.plot_id = p.id ORDER BY c.id DESC LIMIT 1) AS cert_status
        FROM farm_plot p
        WHERE p.status = 'ACTIVE' AND p.boundary_json IS NOT NULL
        ORDER BY p.id
        """
    )
    for plot in plots:
        try:
            plot["boundary"] = json.loads(plot.pop("boundary_json"))
        except (TypeError, json.JSONDecodeError):
            plot["boundary"] = None

    dynamics = _dynamics()
    center = query(
        """
        SELECT AVG(NULLIF(longitude, 0)) AS lng, AVG(NULLIF(latitude, 0)) AS lat
        FROM farm_plot WHERE boundary_json IS NOT NULL
        """
    )[0]
    return {"cards": cards, "map": {"center": center, "plots": plots}, "dynamics": dynamics}


def _dynamics() -> list[dict[str, Any]]:
    """最新业务动态:农事上传/认证/投保/贷款/理赔/认养/订单,合并按时间倒序取前 25 条。"""
    items: list[dict[str, Any]] = []

    rows = query(
        """
        SELECT r.created_at, u.real_name AS who, r.record_type, p.plot_name
        FROM farm_record r
        JOIN sys_user u ON u.id = r.submitted_by
        JOIN farm_plot p ON p.id = r.plot_id
        ORDER BY r.id DESC LIMIT 8
        """
    )
    type_cn = {"SOWING": "播种", "FERTILIZING": "施肥", "PESTICIDE": "打药",
               "IRRIGATION": "灌溉", "HARVEST": "收割", "QUALITY_TEST": "米质检测"}
    items += [
        {
            "time": r["created_at"],
            "type": "农事",
            "text": (
                f"{r['who']} 上传了 {r['plot_name']} 的"
                f"{type_cn.get(r['record_type'], r['record_type'])}记录"
            ),
        }
        for r in rows
    ]

    rows = query(
        """
        SELECT l.applied_at AS at, u.real_name AS who, l.suggested_amount, l.bank_result
        FROM loan_application l JOIN sys_user u ON u.id = (
          SELECT fp.user_id FROM farmer_profile fp WHERE fp.id = l.farmer_id
        ) ORDER BY l.id DESC LIMIT 5
        """
    )
    result_cn = {"PENDING": "待银行审批", "APPROVED": "银行已放款", "REJECTED": "银行未通过"}
    items += [
        {
            "time": r["at"],
            "type": "贷款",
            "text": (
                f"{r['who']} 申请贷款,系统建议 ¥{r['suggested_amount']:.0f},"
                f"{result_cn.get(r['bank_result'], r['bank_result'])}"
            ),
        }
        for r in rows
    ]

    rows = query(
        """
        SELECT i.applied_at AS at, u.real_name AS who, i.insured_amount, p.plot_name
        FROM insurance_policy i
        JOIN farmer_profile f ON f.id = i.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        JOIN farm_plot p ON p.id = i.plot_id
        ORDER BY i.id DESC LIMIT 5
        """
    )
    items += [
        {
            "time": r["at"],
            "type": "投保",
            "text": f"{r['who']} 为 {r['plot_name']} 投保,保额 ¥{r['insured_amount']:.0f}",
        }
        for r in rows
    ]

    rows = query(
        """
        SELECT c.id, u.real_name AS who, c.claim_amount, c.status
        FROM insurance_claim c
        JOIN insurance_policy i ON i.id = c.policy_id
        JOIN farmer_profile f ON f.id = i.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        ORDER BY c.id DESC LIMIT 5
        """
    )
    items += [
        {
            "time": None,
            "type": "理赔",
            "text": f"{r['who']} 的理赔单 ¥{r['claim_amount']:.0f}({r['status']})",
            "id": r["id"],
        }
        for r in rows
    ]

    rows = query(
        """
        SELECT a.started_at AS at, u.real_name AS who, p.plot_name
        FROM adoption_order a
        JOIN sys_user u ON u.id = a.consumer_user_id
        JOIN farm_plot p ON p.id = a.plot_id
        ORDER BY a.id DESC LIMIT 5
        """
    )
    items += [
        {"time": r["at"], "type": "认养", "text": f"消费者 {r['who']} 认养了 {r['plot_name']}"}
        for r in rows
    ]

    rows = query(
        """
        SELECT o.created_at AS at, o.order_no, o.total_amount, o.status
        FROM sales_order o WHERE o.source = 'PLATFORM' AND o.status <> 'CANCELLED'
        ORDER BY o.id DESC LIMIT 5
        """
    )
    items += [
        {"time": r["at"], "type": "订单", "text": f"平台订单 {r['order_no']} ¥{r['total_amount']:.2f}({r['status']})"}
        for r in rows
    ]

    items = [x for x in items if x.get("time")]
    items.sort(key=lambda x: x["time"], reverse=True)
    return items[:25]
