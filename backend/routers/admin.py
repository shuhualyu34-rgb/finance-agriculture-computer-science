"""平台管理/品牌运营:分红计算、认证审批(阶段1最小集)。"""

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.auth import CurrentUser, require_roles
from backend.db import query, query_one, transaction
from backend.rules import DEFAULT_DIVIDEND_RATE, dividend_amount

AdminOnly = require_roles("ADMIN")

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/certifications")
def pending_certifications(user: CurrentUser) -> list[dict[str, Any]]:
    """待审核认证列表(品牌运营端)。"""
    return query(
        """
        SELECT c.*, s.version_no, s.title AS standard_title,
               u.real_name AS farmer_name, u.phone AS farmer_phone,
               p.plot_name, p.plot_code, p.area_mu
        FROM farmer_certification c
        JOIN standard_version s ON s.id = c.standard_id
        JOIN farmer_profile f ON f.id = c.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        JOIN farm_plot p ON p.id = c.plot_id
        WHERE c.status IN ('PENDING','RECTIFYING')
        ORDER BY c.submitted_at LIMIT 200
        """
    )


@router.put("/certifications/{cert_id}/review")
def review_certification(user: CurrentUser, cert_id: int, body: dict[str, str]) -> dict[str, Any]:
    """认证审批:APPROVED / REJECTED / RECTIFYING,通过后同步农户认证状态。"""
    status = body.get("status", "")
    if status not in ("APPROVED", "REJECTED", "RECTIFYING"):
        raise HTTPException(status_code=400, detail="status 只能是 APPROVED、REJECTED 或 RECTIFYING")
    cert = query_one("SELECT * FROM farmer_certification WHERE id = %s", (cert_id,))
    if not cert:
        raise HTTPException(status_code=404, detail="认证申请不存在")
    if cert["status"] != "PENDING" and cert["status"] != "RECTIFYING":
        raise HTTPException(status_code=409, detail="该申请已审结")
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            UPDATE farmer_certification
            SET status = %s, reviewer_id = %s, review_note = %s, reviewed_at = NOW()
            WHERE id = %s
            """,
            (status, user["id"], body.get("note") or None, cert_id),
        )
        if status == "APPROVED":
            # 认证通过 → 农户档案升级为 CERTIFIED(PRD §3.4 品牌认证)
            cursor.execute(
                "UPDATE farmer_profile SET certification_status = 'CERTIFIED', certification_at = NOW() WHERE id = %s",
                (cert["farmer_id"],),
            )
    return {"id": cert_id, "status": status}


@router.post("/dividends/calculate")
def calculate_dividends(user: CurrentUser) -> dict[str, Any]:
    """对已完成且未计提分红的平台引流订单计算农户分红(PRD §12)。"""
    orders = query(
        """
        SELECT o.id, o.total_amount,
               (SELECT i2.plot_id FROM sales_order_item i2 WHERE i2.order_id = o.id LIMIT 1) AS plot_id
        FROM sales_order o
        WHERE o.source = 'PLATFORM' AND o.status = 'COMPLETED'
          AND NOT EXISTS (SELECT 1 FROM farmer_dividend d WHERE d.order_id = o.id)
        ORDER BY o.id LIMIT 100
        """
    )
    created = 0
    total_amount = 0.0
    with transaction() as tx:
        cursor = tx["cursor"]
        for order in orders:
            plot = query_one(
                "SELECT id, farmer_id FROM farm_plot WHERE id = %s", (order["plot_id"],)
            )
            if not plot:
                continue
            amount = dividend_amount(float(order["total_amount"]), float(DEFAULT_DIVIDEND_RATE))
            cursor.execute(
                """
                INSERT INTO farmer_dividend
                  (order_id, farmer_id, plot_id, base_amount, dividend_rate, dividend_amount, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'CALCULATED')
                """,
                (
                    order["id"], plot["farmer_id"], plot["id"],
                    order["total_amount"], float(DEFAULT_DIVIDEND_RATE), amount,
                ),
            )
            created += 1
            total_amount += amount
    return {
        "orders_scanned": len(orders),
        "dividends_created": created,
        "dividend_rate": float(DEFAULT_DIVIDEND_RATE),
        "total_dividend_amount": round(total_amount, 2),
    }


# ---- 系统管理后台(PRD v5 §4.7)----------------------------------------


@router.get("/users")
def users(user: CurrentUser, role: str | None = None, q: str | None = None) -> list[dict[str, Any]]:
    """用户管理:全部角色账号(仅管理员)。"""
    AdminOnly(user)
    sql = """
      SELECT u.id, u.username, u.real_name, u.phone, u.status, u.created_at,
             GROUP_CONCAT(r.role_name) AS roles
      FROM sys_user u
      LEFT JOIN sys_user_role ur ON ur.user_id = u.id
      LEFT JOIN sys_role r ON r.id = ur.role_id
    """
    conds: list[str] = []
    params: list[Any] = []
    if role:
        conds.append(
            "u.id IN (SELECT ur2.user_id FROM sys_user_role ur2"
            " JOIN sys_role r2 ON r2.id = ur2.role_id WHERE r2.role_code = %s)"
        )
        params.append(role)
    if q:
        conds.append("(u.real_name LIKE %s OR u.phone LIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " GROUP BY u.id ORDER BY u.id LIMIT 300"
    return query(sql, tuple(params))


@router.get("/plots")
def admin_plots(user: CurrentUser, adoptable: int | None = None) -> list[dict[str, Any]]:
    """认养管理:地块列表与开放认养状态(仅管理员)。"""
    AdminOnly(user)
    sql = """
      SELECT p.id, p.plot_code, p.plot_name, p.village, p.area_mu, p.variety,
             p.status, p.open_for_adoption,
             (SELECT COUNT(*) FROM adoption_order a
               WHERE a.plot_id = p.id AND a.status IN ('PAID','ACTIVE')) AS adopted_count
      FROM farm_plot p
    """
    params: tuple[Any, ...] = ()
    if adoptable is not None:
        sql += " WHERE p.open_for_adoption = %s"
        params = (adoptable,)
    sql += " ORDER BY p.id LIMIT 500"
    return query(sql, params)


@router.put("/plots/{plot_id}/adoption")
def set_adoption_flag(user: CurrentUser, plot_id: int, body: dict[str, bool]) -> dict[str, Any]:
    """认养管理:开/关某块地的认养(仅管理员)。body: {"open": true|false}"""
    AdminOnly(user)
    plot = query_one("SELECT id FROM farm_plot WHERE id = %s", (plot_id,))
    if not plot:
        raise HTTPException(status_code=404, detail="地块不存在")
    open_flag = 1 if body.get("open") else 0
    with transaction() as tx:
        tx["cursor"].execute(
            "UPDATE farm_plot SET open_for_adoption = %s WHERE id = %s", (open_flag, plot_id)
        )
    return {"id": plot_id, "open_for_adoption": bool(open_flag)}


@router.get("/insurance-products")
def insurance_products() -> list[dict[str, Any]]:
    """数据配置:保险产品参数。"""
    return query("SELECT * FROM insurance_product ORDER BY id")


@router.put("/insurance-products/{product_id}")
def update_insurance_product(
    user: CurrentUser, product_id: int, body: dict[str, Any]
) -> dict[str, Any]:
    """数据配置:调整保额/费率(PRD:保险费率、贷款建议参数可配,仅管理员)。"""
    AdminOnly(user)
    product = query_one("SELECT * FROM insurance_product WHERE id = %s", (product_id,))
    if not product:
        raise HTTPException(status_code=404, detail="保险产品不存在")
    per_mu = body.get("insured_amount_per_mu", product["insured_amount_per_mu"])
    rate = body.get("premium_rate", product["premium_rate"])
    subsidy = body.get("government_subsidy_rate", product["government_subsidy_rate"])
    if not (0 < float(per_mu) and 0 < float(rate) < 1 and 0 <= float(subsidy) < 1):
        raise HTTPException(status_code=400, detail="参数取值不合法")
    with transaction() as tx:
        tx["cursor"].execute(
            """
            UPDATE insurance_product
            SET insured_amount_per_mu = %s, premium_rate = %s, government_subsidy_rate = %s
            WHERE id = %s
            """,
            (per_mu, rate, subsidy, product_id),
        )
    return {
        "id": product_id,
        "insured_amount_per_mu": float(per_mu),
        "premium_rate": float(rate),
        "government_subsidy_rate": float(subsidy),
    }
