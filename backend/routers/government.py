"""政府监管端(PRD v5 §4.6/§11):大屏公开接口 + 监管报表与实地采集(需角色)。
"""

import json
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.auth import CurrentUser, require_roles
from backend.db import query, query_one, transaction

router = APIRouter(prefix="/api/government", tags=["government"])

GovStaff = require_roles("GOVERNMENT", "ADMIN")


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

# ---- 监管报表(PRD v5 §11.4)--------------------------------------------


def _period_bounds(report_type: str, today: date) -> tuple[str, date, date]:
    """返回 (period 标签, 起, 止)。周报=本周一起;月报=本月1日;季报=本季首日。"""
    if report_type == "WEEKLY":
        monday = today - timedelta(days=today.weekday())
        return f"{today.isocalendar().year}-W{today.isocalendar().week:02d}", monday, monday + timedelta(days=6)
    if report_type == "MONTHLY":
        first = today.replace(day=1)
        nxt = (first + timedelta(days=32)).replace(day=1)
        return f"{today.year}-{today.month:02d}", first, nxt - timedelta(days=1)
    if report_type == "QUARTERLY":
        q = (today.month - 1) // 3 + 1
        first = date(today.year, 3 * (q - 1) + 1, 1)
        nxt = date(today.year + (1 if q == 4 else 0), 1 if q == 4 else 3 * q + 1, 1)
        return f"{today.year}-Q{q}", first, nxt - timedelta(days=1)
    raise HTTPException(status_code=400, detail="report_type 只能是 WEEKLY/MONTHLY/QUARTERLY")


def _build_report_content(report_type: str, start: date, end: date) -> dict[str, Any]:
    """汇总一个监管周期的上报内容(PRD §11.4 清单)。"""
    total_farmers = query_one("SELECT COUNT(*) AS n FROM farmer_profile")["n"]
    certified = query_one(
        "SELECT COUNT(*) AS n FROM farmer_profile WHERE certification_status = 'CERTIFIED'"
    )["n"]
    records = query_one(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'NEEDS_CORRECTION' THEN 1 ELSE 0 END) AS wrong
        FROM farm_record WHERE record_date BETWEEN %s AND %s
        """,
        (start, end),
    )
    missing_farmers = query(
        """
        SELECT DISTINCT u.real_name, u.phone, p.plot_name
        FROM farm_record r
        JOIN farm_plot p ON p.id = r.plot_id
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE r.status = 'NEEDS_CORRECTION' AND r.record_date BETWEEN %s AND %s
        ORDER BY u.real_name LIMIT 50
        """,
        (start, end),
    )
    inspections = query_one(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) AS passed,
               SUM(CASE WHEN result IN ('WARNING','FAIL') THEN 1 ELSE 0 END) AS violations
        FROM field_inspection WHERE inspection_date BETWEEN %s AND %s
        """,
        (start, end),
    )
    insurance_stats = query_one(
        """
        SELECT COUNT(*) AS policies,
               COALESCE(SUM(insured_amount), 0) AS insured_amount,
               (SELECT COUNT(*) FROM insurance_claim WHERE reviewed_at BETWEEN %s AND %s) AS claims,
               (SELECT COALESCE(SUM(claim_amount), 0) FROM insurance_claim
                  WHERE reviewed_at BETWEEN %s AND %s AND status = 'PAID') AS paid_amount
        FROM insurance_policy WHERE DATE(applied_at) BETWEEN %s AND %s
        """,
        (start, end, start, end, start, end),
    )
    loans = query_one(
        """
        SELECT COUNT(*) AS applications,
               SUM(CASE WHEN bank_result = 'APPROVED' THEN 1 ELSE 0 END) AS approved,
               COALESCE(SUM(CASE WHEN bank_result = 'APPROVED' THEN suggested_amount ELSE 0 END), 0) AS amount
        FROM loan_application WHERE DATE(applied_at) BETWEEN %s AND %s
        """,
        (start, end),
    )
    sales = query_one(
        """
        SELECT COUNT(*) AS orders, COALESCE(SUM(total_amount), 0) AS amount
        FROM sales_order
        WHERE source = 'PLATFORM' AND status <> 'CANCELLED'
          AND DATE(created_at) BETWEEN %s AND %s
        """,
        (start, end),
    )
    total_records = records["total"] or 0
    wrong_records = records["wrong"] or 0
    insp_total = inspections["total"] or 0
    return {
        "period_range": [start.isoformat(), end.isoformat()],
        "farmers": {"total": total_farmers, "certified": certified},
        "production": {
            "records": total_records,
            "needs_correction": wrong_records,
            "compliance_rate": (
                round((total_records - wrong_records) / total_records * 100, 1) if total_records else None
            ),
            "missing_farmers": missing_farmers,
        },
        "inspections": {
            "total": insp_total,
            "passed": inspections["passed"] or 0,
            "violations": inspections["violations"] or 0,
            "rectification_rate": round((inspections["passed"] or 0) / insp_total * 100, 1) if insp_total else None,
        },
        "insurance": insurance_stats,
        "loans": loans,
        "sales": sales,
    }


@router.post("/reports/generate", status_code=201)
def generate_report(user: CurrentUser, body: dict[str, str]) -> dict[str, Any]:
    """生成(或按周期幂等重建)监管报表。body: {"report_type": "WEEKLY|MONTHLY|QUARTERLY"}"""
    GovStaff(user)
    report_type = body.get("report_type", "WEEKLY")
    period, start, end = _period_bounds(report_type, date.today())
    content = _build_report_content(report_type, start, end)
    existing = query_one(
        "SELECT id FROM regulatory_report WHERE report_type = %s AND report_period = %s",
        (report_type, period),
    )
    with transaction() as tx:
        cursor = tx["cursor"]
        if existing:
            cursor.execute(
                "UPDATE regulatory_report SET content_json = %s WHERE id = %s",
                (json.dumps(content, ensure_ascii=False, default=str), existing["id"]),
            )
            report_id, created = existing["id"], False
        else:
            cursor.execute(
                """
                INSERT INTO regulatory_report (report_type, report_period, content_json, status)
                VALUES (%s, %s, %s, 'DRAFT')
                """,
                (report_type, period, json.dumps(content, ensure_ascii=False, default=str)),
            )
            report_id, created = cursor.lastrowid, True
    return {
        "id": report_id,
        "report_type": report_type,
        "report_period": period,
        "created": created,
        "status": "DRAFT" if created else "已重建(DRAFT)",
    }


@router.get("/reports")
def list_reports(user: CurrentUser, report_type: str | None = None) -> list[dict[str, Any]]:
    """历史上报留档。"""
    GovStaff(user)
    sql = "SELECT id, report_type, report_period, status, confirmed_at, created_at FROM regulatory_report"
    params: tuple[Any, ...] = ()
    if report_type:
        sql += " WHERE report_type = %s"
        params = (report_type,)
    sql += " ORDER BY id DESC LIMIT 100"
    return query(sql, params)


@router.get("/reports/{report_id}")
def report_detail(user: CurrentUser, report_id: int) -> dict[str, Any]:
    """报表详情(含汇总内容与备注)。"""
    GovStaff(user)
    row = query_one("SELECT * FROM regulatory_report WHERE id = %s", (report_id,))
    if not row:
        raise HTTPException(status_code=404, detail="报表不存在")
    row["content"] = json.loads(row.pop("content_json"))
    return row


@router.put("/reports/{report_id}/confirm")
def confirm_report(user: CurrentUser, report_id: int, body: dict[str, str]) -> dict[str, Any]:
    """政府端预览确认,可补充现场检查备注;确认后留档(PRD §11.4 上报流程)。"""
    GovStaff(user)
    row = query_one("SELECT * FROM regulatory_report WHERE id = %s", (report_id,))
    if not row:
        raise HTTPException(status_code=404, detail="报表不存在")
    if row["status"] == "ARCHIVED":
        raise HTTPException(status_code=409, detail="该报表已归档,不能修改")
    note = body.get("note", "")
    content = json.loads(row["content_json"])
    if note:
        content["site_note"] = note
    with transaction() as tx:
        tx["cursor"].execute(
            """
            UPDATE regulatory_report
            SET content_json = %s, status = 'CONFIRMED', confirmed_by = %s, confirmed_at = NOW()
            WHERE id = %s
            """,
            (json.dumps(content, ensure_ascii=False, default=str), user["id"], report_id),
        )
    return {"id": report_id, "status": "CONFIRMED"}


# ---- 实地采集(PRD v5 §11.5)--------------------------------------------


@router.post("/inspections", status_code=201)
def create_inspection(user: CurrentUser, body: dict[str, Any]) -> dict[str, Any]:
    """政府实地采集录入:田间查看/面积核实/投入品检查等。

    body: {plot_id, inspection_date, result: PASS|WARNING|FAIL,
           actual_area_mu?, difference_note?, rectification_required?}
    actual_area_mu 与申报面积差异 >20% 时自动标 WARNING 并记录差异。
    """
    GovStaff(user)
    plot = query_one("SELECT * FROM farm_plot WHERE id = %s", (body.get("plot_id"),))
    if not plot:
        raise HTTPException(status_code=404, detail="地块不存在")
    result = body.get("result", "PASS")
    if result not in ("PASS", "WARNING", "FAIL"):
        raise HTTPException(status_code=400, detail="result 只能是 PASS/WARNING/FAIL")
    try:
        insp_date = date.fromisoformat(body.get("inspection_date") or date.today().isoformat())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="inspection_date 需为 YYYY-MM-DD") from exc

    note = body.get("difference_note") or ""
    auto_flag = False
    actual = body.get("actual_area_mu")
    if actual is not None:
        declared = float(plot["area_mu"])
        diff = abs(float(actual) - declared) / declared if declared else 0
        if diff > 0.20:
            auto_flag = True
            if result == "PASS":
                result = "WARNING"
            note = (note + "; " if note else "") + (
                f"面积交叉核验:申报 {declared} 亩,实测 {actual} 亩,差异 {diff * 100:.1f}%(>20% 自动预警)"
            )
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO field_inspection
              (plot_id, inspector_id, inspection_date, result, difference_note, rectification_required)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                plot["id"], user["id"], insp_date, result, note or None,
                1 if (body.get("rectification_required") or auto_flag) else 0,
            ),
        )
        insp_id = cursor.lastrowid
    return {
        "id": insp_id,
        "plot_id": plot["id"],
        "result": result,
        "auto_warning": auto_flag,
        "note": note,
    }


@router.get("/inspections")
def list_inspections(user: CurrentUser, plot_id: int | None = None) -> list[dict[str, Any]]:
    """实地采集留痕记录(含采集人与地块)。"""
    GovStaff(user)
    sql = """
      SELECT i.*, p.plot_name, p.plot_code, p.village, u.real_name AS inspector_name
      FROM field_inspection i
      JOIN farm_plot p ON p.id = i.plot_id
      JOIN sys_user u ON u.id = i.inspector_id
    """
    params: tuple[Any, ...] = ()
    if plot_id:
        sql += " WHERE i.plot_id = %s"
        params = (plot_id,)
    sql += " ORDER BY i.id DESC LIMIT 200"
    return query(sql, params)

