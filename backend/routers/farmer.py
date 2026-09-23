"""农户端(H5):农事上传、认证/保险/贷款申请、我的收入与分红。"""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.auth import CurrentUser, require_roles
from backend.db import query, query_one, transaction
from backend.rules import loan_suggestion, product_quote, risk_level
from backend.schemas import CertificationCreate, FarmRecordCreate, InsuranceApply, LoanApply

router = APIRouter(prefix="/api/my", tags=["farmer"])

FarmerUser = require_roles("FARMER")

RECORD_TYPES = {"SOWING", "FERTILIZING", "PESTICIDE", "IRRIGATION", "HARVEST", "QUALITY_TEST"}


def farmer_profile(user: dict[str, Any]) -> dict[str, Any]:
    row = query_one("SELECT * FROM farmer_profile WHERE user_id = %s", (user["id"],))
    if not row:
        raise HTTPException(status_code=403, detail="当前账号没有农户档案")
    return row


def own_plot(farmer_id: int, plot_id: int) -> dict[str, Any]:
    row = query_one(
        "SELECT * FROM farm_plot WHERE id = %s AND farmer_id = %s",
        (plot_id, farmer_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail="地块不存在或不属于当前农户")
    return row


def current_season() -> dict[str, Any]:
    row = query_one(
        "SELECT * FROM production_season WHERE status = 'IN_PROGRESS' ORDER BY id DESC LIMIT 1"
    )
    if not row:
        row = query_one("SELECT * FROM production_season ORDER BY id DESC LIMIT 1")
    if not row:
        raise HTTPException(status_code=503, detail="系统缺少种植季数据")
    return row


def next_no(prefix: str) -> str:
    # 日期 + 8 位十六进制随机后缀,避免同日并发撞 UNIQUE 约束
    return f"{prefix}{date.today().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


@router.get("/summary")
def my_summary(user: CurrentUser) -> dict[str, Any]:
    farmer = farmer_profile(user)
    fid = farmer["id"]
    latest_loan = query_one(
        """
        SELECT application_no, area_mu, suggested_amount, risk_level, bank_result, applied_at
        FROM loan_application WHERE farmer_id = %s ORDER BY id DESC LIMIT 1
        """,
        (fid,),
    )
    dividends = query_one(
        """
        SELECT COALESCE(SUM(dividend_amount), 0) AS total,
               COALESCE(SUM(CASE WHEN status <> 'SETTLED' THEN dividend_amount ELSE 0 END), 0) AS pending
        FROM farmer_dividend WHERE farmer_id = %s
        """,
        (fid,),
    )
    plots = query_one(
        """
        SELECT COUNT(*) AS plot_count, COALESCE(SUM(area_mu), 0) AS total_area_mu
        FROM farm_plot WHERE farmer_id = %s AND status = 'ACTIVE'
        """,
        (fid,),
    )
    policies = query_one(
        """
        SELECT COUNT(*) AS policy_count,
               COALESCE(SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END), 0) AS active_count
        FROM insurance_policy WHERE farmer_id = %s
        """,
        (fid,),
    )
    return {
        "farmer": farmer,
        "plots": plots,
        "policies": policies,
        "latest_loan": latest_loan,
        "dividends": dividends,
    }


@router.get("/plots")
def my_plots(user: CurrentUser) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    return query(
        """
        SELECT p.*,
               (SELECT c2.status FROM farmer_certification c2
                 WHERE c2.plot_id = p.id ORDER BY c2.id DESC LIMIT 1) AS cert_status
        FROM farm_plot p
        WHERE p.farmer_id = %s AND p.status = 'ACTIVE'
        ORDER BY p.id
        """,
        (farmer["id"],),
    )


@router.get("/records")
def my_records(user: CurrentUser, plot_id: int | None = Query(default=None)) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    sql = """
      SELECT r.*, p.plot_name, p.plot_code,
             (SELECT GROUP_CONCAT(a.file_url) FROM record_attachment a WHERE a.record_id = r.id) AS photo_urls
      FROM farm_record r
      JOIN farm_plot p ON p.id = r.plot_id
      WHERE p.farmer_id = %s
    """
    params: list[Any] = [farmer["id"]]
    if plot_id:
        sql += " AND r.plot_id = %s"
        params.append(plot_id)
    sql += " ORDER BY r.record_date DESC, r.id DESC LIMIT 200"
    return query(sql, tuple(params))


@router.post("/records", status_code=201)
def create_record(user: CurrentUser, body: FarmRecordCreate) -> dict[str, Any]:
    farmer = farmer_profile(user)
    plot = own_plot(farmer["id"], body.plot_id)
    if body.record_type not in RECORD_TYPES:
        raise HTTPException(status_code=400, detail=f"record_type 必须是 {sorted(RECORD_TYPES)} 之一")
    try:
        record_date = date.fromisoformat(body.record_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="record_date 需为 YYYY-MM-DD") from exc
    if record_date > date.today():
        raise HTTPException(status_code=400, detail="记录日期不能晚于今天")
    season = current_season()
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO farm_record
              (plot_id, season_id, record_type, record_date, description,
               material_name, material_amount, output_jin, submitted_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'SUBMITTED')
            """,
            (
                plot["id"], season["id"], body.record_type, body.record_date,
                body.description or None, body.material_name, body.material_amount,
                body.output_jin, user["id"],
            ),
        )
        record_id = cursor.lastrowid
        for url in body.photo_urls[:9]:
            cursor.execute(
                "INSERT INTO record_attachment (record_id, file_url, file_type) VALUES (%s, %s, %s)",
                (record_id, url, "IMAGE"),
            )
    return {"id": record_id, "plot_id": plot["id"], "season_id": season["id"], "status": "SUBMITTED"}


@router.get("/certifications")
def my_certifications(user: CurrentUser) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    return query(
        """
        SELECT c.*, s.version_no, s.title AS standard_title, p.plot_name
        FROM farmer_certification c
        JOIN standard_version s ON s.id = c.standard_id
        JOIN farm_plot p ON p.id = c.plot_id
        WHERE c.farmer_id = %s ORDER BY c.id DESC
        """,
        (farmer["id"],),
    )


@router.post("/certifications", status_code=201)
def create_certification(user: CurrentUser, body: CertificationCreate) -> dict[str, Any]:
    farmer = farmer_profile(user)
    plot = own_plot(farmer["id"], body.plot_id)
    pending = query_one(
        "SELECT id FROM farmer_certification WHERE plot_id = %s AND status IN ('PENDING','RECTIFYING')",
        (plot["id"],),
    )
    if pending:
        raise HTTPException(status_code=409, detail="该地块已有待审核的认证申请")
    standard = query_one(
        "SELECT * FROM standard_version WHERE status = 'PUBLISHED' ORDER BY id DESC LIMIT 1"
    ) or query_one("SELECT * FROM standard_version ORDER BY id DESC LIMIT 1")
    if not standard:
        raise HTTPException(status_code=503, detail="系统尚未配置认证标准")
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO farmer_certification (farmer_id, plot_id, standard_id, status, review_note)
            VALUES (%s, %s, %s, 'PENDING', %s)
            """,
            (farmer["id"], plot["id"], standard["id"], body.note or None),
        )
        cert_id = cursor.lastrowid
    return {"id": cert_id, "plot_id": plot["id"], "standard_id": standard["id"], "status": "PENDING"}


@router.get("/policies")
def my_policies(user: CurrentUser) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    return query(
        """
        SELECT i.*, p.plot_name, pr.product_code, pr.product_type, pr.product_name
        FROM insurance_policy i
        JOIN farm_plot p ON p.id = i.plot_id
        JOIN insurance_product pr ON pr.id = i.product_id
        WHERE i.farmer_id = %s ORDER BY i.id DESC
        """,
        (farmer["id"],),
    )


@router.get("/insurance-products")
def my_insurance_products(user: CurrentUser) -> list[dict[str, Any]]:
    return query(
        "SELECT id, product_code, product_type, product_name, insured_amount_per_mu, premium_rate, "
        "government_subsidy_rate, trigger_config, description FROM insurance_product "
        "WHERE status = 'ACTIVE' ORDER BY id"
    )


@router.post("/insurance", status_code=201)
def apply_insurance(user: CurrentUser, body: InsuranceApply) -> dict[str, Any]:
    farmer = farmer_profile(user)
    plot = own_plot(farmer["id"], body.plot_id)
    product = query_one(
        "SELECT * FROM insurance_product WHERE id = %s AND status = 'ACTIVE'", (body.product_id,)
    )
    if not product:
        raise HTTPException(status_code=404, detail="保险产品不存在或已下架")
    quote = product_quote(float(plot["area_mu"]), product)
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO insurance_policy
              (policy_no, farmer_id, plot_id, product_id, insured_area_mu,
               insured_amount, total_premium, farmer_premium, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'APPLIED')
            """,
            (
                next_no("BO"), farmer["id"], plot["id"], product["id"], plot["area_mu"],
                quote["insured_amount"], quote["total_premium"], quote["farmer_premium"],
            ),
        )
        policy_id = cursor.lastrowid
    return {"id": policy_id, "quote": quote, "status": "APPLIED"}


@router.get("/loans")
def my_loans(user: CurrentUser) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    return query(
        """
        SELECT l.*, p.plot_name FROM loan_application l
        JOIN farm_plot p ON p.id = l.plot_id
        WHERE l.farmer_id = %s ORDER BY l.id DESC
        """,
        (farmer["id"],),
    )


@router.post("/loans", status_code=201)
def apply_loan(user: CurrentUser, body: LoanApply) -> dict[str, Any]:
    farmer = farmer_profile(user)
    plot = own_plot(farmer["id"], body.plot_id)
    certified = farmer["certification_status"] == "CERTIFIED"
    has_insurance = bool(
        query_one(
            "SELECT id FROM insurance_policy WHERE farmer_id = %s AND status IN ('APPLIED','ACTIVE') LIMIT 1",
            (farmer["id"],),
        )
    )
    profile_complete = farmer["address"] is not None and farmer["id_card_masked"] is not None
    suggested = loan_suggestion(float(plot["area_mu"]))
    risk = risk_level(certified, has_insurance, profile_complete)
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO loan_application
              (application_no, farmer_id, plot_id, area_mu, suggested_amount, risk_level, bank_result)
            VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
            """,
            (next_no("DK"), farmer["id"], plot["id"], plot["area_mu"], suggested, risk),
        )
        loan_id = cursor.lastrowid
    return {
        "id": loan_id,
        "suggested_amount": suggested,
        "risk_level": risk,
        "basis": {"certified": certified, "has_insurance": has_insurance, "profile_complete": profile_complete},
        "note": "系统建议仅供参考,最终由银行自行决定",
    }


@router.get("/claims")
def my_claims(user: CurrentUser) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    return query(
        """
        SELECT c.*, i.policy_no, p.plot_name
        FROM insurance_claim c
        JOIN insurance_policy i ON i.id = c.policy_id
        JOIN farm_plot p ON p.id = i.plot_id
        WHERE i.farmer_id = %s ORDER BY c.id DESC
        """,
        (farmer["id"],),
    )


@router.get("/dividends")
def my_dividends(user: CurrentUser) -> list[dict[str, Any]]:
    farmer = farmer_profile(user)
    return query(
        """
        SELECT d.*, o.order_no, o.total_amount AS order_amount, p.plot_name
        FROM farmer_dividend d
        JOIN sales_order o ON o.id = d.order_id
        JOIN farm_plot p ON p.id = d.plot_id
        WHERE d.farmer_id = %s ORDER BY d.id DESC
        """,
        (farmer["id"],),
    )

@router.get("/income")
def my_income(user: CurrentUser, year: str | None = Query(default=None)) -> dict[str, Any]:
    """我的收入(PRD §4.1):地租 + 工资 + 品牌溢价 + 平台销售分红,按年汇总。"""
    farmer = farmer_profile(user)
    fid = farmer["id"]
    year = year or str(date.today().year)
    items = query(
        """
        SELECT income_type, amount, period, remark, created_at, 'INCOME' AS source
        FROM farmer_income WHERE farmer_id = %s AND period = %s
        UNION ALL
        SELECT 'DIVIDEND' AS income_type, d.dividend_amount AS amount,
               YEAR(COALESCE(d.settled_at, o.completed_at)) AS period,
               CONCAT('平台引流订单 ', o.order_no) AS remark,
               COALESCE(d.settled_at, o.completed_at) AS created_at, 'DIVIDEND' AS source
        FROM farmer_dividend d
        JOIN sales_order o ON o.id = d.order_id
        WHERE d.farmer_id = %s AND YEAR(COALESCE(d.settled_at, o.completed_at)) = %s
        ORDER BY created_at DESC
        """,
        (fid, year, fid, year),
    )
    summary = {k: 0.0 for k in ("RENT", "WAGE", "BRAND_PREMIUM", "DIVIDEND")}
    for it in items:
        summary[it["income_type"]] = round(summary.get(it["income_type"], 0) + float(it["amount"]), 2)
    summary["TOTAL"] = round(sum(summary.values()), 2)
    return {"year": year, "summary": summary, "items": items}
