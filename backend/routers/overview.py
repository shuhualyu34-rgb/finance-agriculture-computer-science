"""总览与各端只读接口(阶段 1 既有能力,路径保持不变)。"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.db import query

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, Any]:
    rows = query("SELECT DATABASE() AS database_name, VERSION() AS version")
    return {"status": "ok", "database": rows[0]}


@router.get("/dashboard/summary")
def dashboard_summary() -> dict[str, Any]:
    rows = query(
        """
        SELECT
          (SELECT COUNT(*) FROM farmer_profile) AS farmers,
          (SELECT COUNT(*) FROM farm_plot WHERE status = 'ACTIVE') AS active_plots,
          (SELECT COUNT(*) FROM farm_record) AS production_records,
          (SELECT COUNT(*) FROM insurance_policy WHERE status = 'ACTIVE') AS active_policies,
          (SELECT COUNT(*) FROM loan_application) AS loan_applications,
          (SELECT COUNT(*) FROM adoption_order WHERE status IN ('PAID','ACTIVE')) AS active_adoptions,
          (SELECT COUNT(*) FROM sales_order WHERE status <> 'CANCELLED') AS orders,
          (SELECT COALESCE(SUM(total_amount), 0) FROM sales_order
             WHERE source = 'PLATFORM' AND status <> 'CANCELLED') AS sales_amount,
          (SELECT COALESCE(SUM(dividend_amount), 0) FROM farmer_dividend WHERE status <> 'SETTLED') AS pending_dividend
        """
    )
    return rows[0]


@router.get("/farmers")
def farmers(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = """
      SELECT f.id, u.real_name, u.phone, f.village, f.certification_status,
             COUNT(DISTINCT p.id) AS plot_count,
             COALESCE(SUM(p.area_mu), 0) AS total_area_mu
      FROM farmer_profile f
      JOIN sys_user u ON u.id = f.user_id
      LEFT JOIN farm_plot p ON p.farmer_id = f.id AND p.status = 'ACTIVE'
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE f.certification_status = %s"
        params = (status,)
    sql += " GROUP BY f.id, u.real_name, u.phone, f.village, f.certification_status ORDER BY f.id"
    return query(sql, params)


@router.get("/plots/{plot_id}")
def plot_detail(plot_id: int) -> dict[str, Any]:
    plots = query(
        """
        SELECT p.*, u.real_name AS farmer_name, u.phone AS farmer_phone
        FROM farm_plot p
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE p.id = %s
        """,
        (plot_id,),
    )
    if not plots:
        raise HTTPException(status_code=404, detail="地块不存在")
    result = plots[0]
    result["records"] = query(
        """
        SELECT id, record_type, record_date, description, material_name,
               material_amount, output_jin, status
        FROM farm_record WHERE plot_id = %s ORDER BY record_date DESC, id DESC
        """,
        (plot_id,),
    )
    result["certifications"] = query(
        """
        SELECT c.id, c.status, c.review_note, s.version_no, s.title
        FROM farmer_certification c
        JOIN standard_version s ON s.id = c.standard_id
        WHERE c.plot_id = %s ORDER BY c.id DESC
        """,
        (plot_id,),
    )
    return result


@router.get("/trace/{code}")
def traceability(code: str) -> dict[str, Any]:
    rows = query(
        """
        SELECT t.id, t.code, t.batch_name, t.product_grade, t.quality_report_url,
               p.id AS plot_id, p.plot_code, p.plot_name, p.village, p.area_mu,
               p.variety, p.longitude, p.latitude, p.satellite_image_url,
               u.real_name AS farmer_name
        FROM trace_code t
        JOIN farm_plot p ON p.id = t.plot_id
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE t.code = %s AND t.status = 'ACTIVE'
        """,
        (code,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="溯源码不存在或已失效")
    result = rows[0]
    result["production_records"] = query(
        """
        SELECT record_type, record_date, description, material_name,
               material_amount, output_jin
        FROM farm_record WHERE plot_id = %s ORDER BY record_date ASC, id ASC
        """,
        (result["plot_id"],),
    )
    return result


@router.get("/loans")
def loans(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = """
      SELECT l.*, u.real_name AS farmer_name, p.plot_name
      FROM loan_application l
      JOIN farmer_profile f ON f.id = l.farmer_id
      JOIN sys_user u ON u.id = f.user_id
      JOIN farm_plot p ON p.id = l.plot_id
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE l.bank_result = %s"
        params = (status,)
    sql += " ORDER BY l.applied_at DESC"
    return query(sql, params)


@router.get("/claims")
def claims(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = """
      SELECT c.*, i.policy_no, u.real_name AS farmer_name, p.plot_name
      FROM insurance_claim c
      JOIN insurance_policy i ON i.id = c.policy_id
      JOIN farmer_profile f ON f.id = i.farmer_id
      JOIN sys_user u ON u.id = f.user_id
      JOIN farm_plot p ON p.id = i.plot_id
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE c.status = %s"
        params = (status,)
    sql += " ORDER BY c.id DESC"
    return query(sql, params)


@router.get("/orders")
def orders(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = """
      SELECT o.id, o.order_no, o.total_amount, o.source, o.status, o.created_at,
             u.real_name AS consumer_name, sh.carrier, sh.tracking_no
      FROM sales_order o
      LEFT JOIN sys_user u ON u.id = o.consumer_user_id
      LEFT JOIN shipment sh ON sh.order_id = o.id
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE o.status = %s"
        params = (status,)
    sql += " ORDER BY o.created_at DESC"
    return query(sql, params)


@router.get("/government/summary")
def government_summary() -> dict[str, Any]:
    rows = query(
        """
        SELECT
          (SELECT COUNT(*) FROM farmer_profile WHERE certification_status = 'CERTIFIED') AS certified_farmers,
          (SELECT COUNT(*) FROM field_inspection WHERE result IN ('WARNING','FAIL')) AS inspection_warnings,
          (SELECT COUNT(*) FROM farm_record WHERE status = 'NEEDS_CORRECTION') AS missing_or_wrong_records,
          (SELECT COUNT(*) FROM regulatory_report WHERE status = 'DRAFT') AS pending_reports
        """
    )
    return rows[0]
