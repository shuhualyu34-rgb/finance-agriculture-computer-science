"""消费端(H5):可认养地块、认养下单(模拟支付)、我的认养。"""

import random
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.auth import CurrentUser, require_roles
from backend.db import query, query_one, transaction
from backend.schemas import AdoptionCreate

router = APIRouter(prefix="/api", tags=["consumer"])

ConsumerUser = require_roles("CONSUMER")


@router.get("/my/adoptions")
def my_adoptions(user: CurrentUser) -> list[dict[str, Any]]:
    """我的认养列表(消费端)。"""
    return query(
        """
        SELECT a.id, a.order_no, a.fee, a.status, a.started_at,
               p.plot_name, p.plot_code, p.village, p.area_mu, p.variety,
               p.satellite_image_url, u.real_name AS farmer_name,
               (SELECT COUNT(*) FROM farm_record r
                 WHERE r.plot_id = p.id
                   AND r.record_date >= a.started_at) AS updates_since_adopted
        FROM adoption_order a
        JOIN farm_plot p ON p.id = a.plot_id
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE a.consumer_user_id = %s
        ORDER BY a.id DESC
        """,
        (user["id"],),
    )

# 认养费(MVP):面积 × 100 元/亩,最低 199 元
ADOPTION_FEE_PER_MU = 100
ADOPTION_FEE_MIN = 199


@router.get("/adoption/plots")
def adoption_plots(user: CurrentUser) -> list[dict[str, Any]]:
    """可认养地块列表(登录即可浏览,含已认养标记)。"""
    rows = query(
        """
        SELECT p.id, p.plot_code, p.plot_name, p.village, p.area_mu, p.variety,
               p.satellite_image_url, u.real_name AS farmer_name,
               (SELECT COUNT(*) FROM adoption_order a
                 WHERE a.plot_id = p.id AND a.status IN ('PAID','ACTIVE')) AS adopted_count
        FROM farm_plot p
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE p.status = 'ACTIVE' AND p.open_for_adoption = 1
        ORDER BY p.id LIMIT 50
        """
    )
    for row in rows:
        row["adoption_fee"] = max(ADOPTION_FEE_MIN, round(float(row["area_mu"]) * ADOPTION_FEE_PER_MU))
    return rows


@router.post("/adoption/orders", status_code=201)
def create_adoption(user: CurrentUser, body: AdoptionCreate) -> dict[str, Any]:
    consumer = require_roles("CONSUMER")(user)
    plot = query_one(
        "SELECT * FROM farm_plot WHERE id = %s AND status = 'ACTIVE' AND open_for_adoption = 1",
        (body.plot_id,),
    )
    if not plot:
        raise HTTPException(status_code=404, detail="地块不存在或未开放认养")
    active = query_one(
        """
        SELECT id FROM adoption_order
        WHERE consumer_user_id = %s AND plot_id = %s AND status IN ('PAID','ACTIVE') LIMIT 1
        """,
        (consumer["id"], plot["id"]),
    )
    if active:
        raise HTTPException(status_code=409, detail="您已认养该地块,无需重复认养")
    fee = max(ADOPTION_FEE_MIN, round(float(plot["area_mu"]) * ADOPTION_FEE_PER_MU))
    order_no = f"AY{date.today().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO adoption_order (order_no, consumer_user_id, plot_id, fee, status)
            VALUES (%s, %s, %s, %s, 'PAID')
            """,
            (order_no, consumer["id"], plot["id"], fee),
        )
        order_id = cursor.lastrowid
    # PRD v5 §八:Demo 模拟支付,点确认即完成,故直接 PAID
    return {"id": order_id, "order_no": order_no, "fee": fee, "status": "PAID", "paid": True}
