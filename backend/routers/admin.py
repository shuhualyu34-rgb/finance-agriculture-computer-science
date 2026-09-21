"""平台管理/品牌运营:分红计算、认证审批(阶段1最小集)。"""

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.auth import CurrentUser
from backend.db import query, query_one, transaction
from backend.rules import DEFAULT_DIVIDEND_RATE, dividend_amount

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
