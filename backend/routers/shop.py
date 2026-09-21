"""在线商城(PRD v5 §12):下单(模拟支付)、我的订单、运营端订单处理与分红依据。"""

import random
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.auth import CurrentUser, require_roles
from backend.db import query, query_one, transaction

router = APIRouter(prefix="/api/shop", tags=["shop"])

ConsumerUser = require_roles("CONSUMER")
OperatorUser = require_roles("OPERATOR", "ADMIN")


@router.get("/products")
def products() -> list[dict[str, Any]]:
    """商城首页:在售商品(含地块溯源信息)。"""
    return query(
        """
        SELECT pr.id, pr.product_name, pr.specification, pr.price, pr.stock,
               t.code AS trace_code, t.product_grade,
               p.plot_name, p.village, u.real_name AS farmer_name
        FROM product pr
        JOIN trace_code t ON t.id = pr.trace_code_id
        JOIN farm_plot p ON p.id = t.plot_id
        JOIN farmer_profile f ON f.id = p.farmer_id
        JOIN sys_user u ON u.id = f.user_id
        WHERE pr.status = 'ON_SALE'
        ORDER BY pr.id LIMIT 100
        """
    )


def _next_order_no() -> str:
    return f"SO{date.today().strftime('%Y%m%d')}{random.randint(1000, 9999)}"


@router.post("/orders", status_code=201)
def create_order(user: CurrentUser, body: dict[str, Any]) -> dict[str, Any]:
    """下单:items=[{product_id, quantity}],地址 {receiver, phone, detail_address}。"""
    consumer = ConsumerUser(user)
    items = body.get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="购物车为空")
    receiver = (body.get("receiver") or "").strip()
    phone = (body.get("phone") or "").strip()
    detail = (body.get("detail_address") or "").strip()
    if not receiver or not phone or not detail:
        raise HTTPException(status_code=400, detail="请填写完整的收货人、电话和地址")

    resolved: list[dict[str, Any]] = []
    total = 0.0
    for it in items:
        qty = int(it.get("quantity") or 0)
        if qty < 1 or qty > 99:
            raise HTTPException(status_code=400, detail="购买数量需在 1-99 之间")
        product = query_one(
            "SELECT pr.*, t.plot_id FROM product pr JOIN trace_code t ON t.id = pr.trace_code_id"
            " WHERE pr.id = %s AND pr.status = 'ON_SALE'",
            (it.get("product_id"),),
        )
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 {it.get('product_id')} 不存在或已下架")
        if product["stock"] < qty:
            raise HTTPException(status_code=400, detail=f"{product['product_name']} 库存不足")
        amount = round(float(product["price"]) * qty, 2)
        total += amount
        resolved.append({"product": product, "qty": qty, "amount": amount})
    total = round(total, 2)

    order_no = _next_order_no()
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO sales_order
              (order_no, consumer_user_id, total_amount, source, status, address_snapshot)
            VALUES (%s, %s, %s, 'PLATFORM', 'PENDING_PAYMENT', %s)
            """,
            (
                order_no, consumer["id"], total,
                f'{{"receiver": "{receiver}", "phone": "{phone}", "detail_address": "{detail}"}}',
            ),
        )
        order_id = cursor.lastrowid
        for r in resolved:
            cursor.execute(
                """
                INSERT INTO sales_order_item (order_id, product_id, plot_id, quantity, unit_price, amount)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id, r["product"]["id"], r["product"]["plot_id"],
                    r["qty"], r["product"]["price"], r["amount"],
                ),
            )
            cursor.execute(
                "UPDATE product SET stock = stock - %s WHERE id = %s",
                (r["qty"], r["product"]["id"]),
            )
        cursor.execute(
            "INSERT INTO shipment (order_id) VALUES (%s)", (order_id,)
        )
    return {"id": order_id, "order_no": order_no, "total_amount": total, "status": "PENDING_PAYMENT"}


def _own_order(user_id: int, order_id: int) -> dict[str, Any]:
    row = query_one(
        "SELECT * FROM sales_order WHERE id = %s AND consumer_user_id = %s",
        (order_id, user_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail="订单不存在")
    return row


@router.post("/orders/{order_id}/pay")
def pay_order(user: CurrentUser, order_id: int) -> dict[str, Any]:
    """模拟支付(PRD §八:点确认即完成)。"""
    consumer = ConsumerUser(user)
    order = _own_order(consumer["id"], order_id)
    if order["status"] != "PENDING_PAYMENT":
        raise HTTPException(status_code=409, detail="订单状态不允许支付")
    with transaction() as tx:
        tx["cursor"].execute(
            "UPDATE sales_order SET status = 'PAID', paid_at = NOW() WHERE id = %s", (order_id,)
        )
    return {"id": order_id, "status": "PAID"}


@router.post("/orders/{order_id}/confirm")
def confirm_order(user: CurrentUser, order_id: int) -> dict[str, Any]:
    """确认收货:SHIPPED -> COMPLETED(分红计算依据)。"""
    consumer = ConsumerUser(user)
    order = _own_order(consumer["id"], order_id)
    if order["status"] != "SHIPPED":
        raise HTTPException(status_code=409, detail="订单尚未发货,无法确认收货")
    with transaction() as tx:
        tx["cursor"].execute(
            "UPDATE sales_order SET status = 'COMPLETED', completed_at = NOW() WHERE id = %s",
            (order_id,),
        )
    return {"id": order_id, "status": "COMPLETED"}


@router.get("/my-orders")
def my_orders(user: CurrentUser) -> list[dict[str, Any]]:
    """我的订单(消费端),含商品明细与物流。"""
    orders = query(
        """
        SELECT o.*, sh.carrier, sh.tracking_no, sh.shipped_at
        FROM sales_order o
        LEFT JOIN shipment sh ON sh.order_id = o.id
        WHERE o.consumer_user_id = %s
        ORDER BY o.id DESC LIMIT 100
        """,
        (user["id"],),
    )
    for o in orders:
        o["items"] = query(
            """
            SELECT i.quantity, i.unit_price, i.amount, pr.product_name, pr.specification
            FROM sales_order_item i JOIN product pr ON pr.id = i.product_id
            WHERE i.order_id = %s
            """,
            (o["id"],),
        )
    return orders


# ---- 品牌运营端订单管理(PRD §12.3)----


@router.get("/orders")
def all_orders(user: CurrentUser, status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """订单列表(运营端,区分平台引流订单)。"""
    OperatorUser(user)
    sql = """
      SELECT o.*, u.real_name AS consumer_name, u.phone AS consumer_phone,
             sh.carrier, sh.tracking_no,
             (SELECT GROUP_CONCAT(pr.product_name SEPARATOR '、')
                FROM sales_order_item i JOIN product pr ON pr.id = i.product_id
               WHERE i.order_id = o.id) AS product_summary
      FROM sales_order o
      LEFT JOIN sys_user u ON u.id = o.consumer_user_id
      LEFT JOIN shipment sh ON sh.order_id = o.id
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE o.status = %s"
        params = (status,)
    sql += " ORDER BY o.id DESC LIMIT 200"
    return query(sql, params)


@router.put("/orders/{order_id}/ship")
def ship_order(user: CurrentUser, order_id: int, body: dict[str, str]) -> dict[str, Any]:
    """录入物流单号并发货(通知合作企业代发后)。"""
    order = query_one("SELECT * FROM sales_order WHERE id = %s", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order["status"] != "PAID":
        raise HTTPException(status_code=409, detail="仅已支付订单可发货")
    carrier = (body.get("carrier") or "").strip()
    tracking = (body.get("tracking_no") or "").strip()
    if not carrier or not tracking:
        raise HTTPException(status_code=400, detail="请填写快递公司和单号")
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            "UPDATE sales_order SET status = 'SHIPPED', shipped_at = NOW() WHERE id = %s",
            (order_id,),
        )
        cursor.execute(
            """
            INSERT INTO shipment (order_id, carrier, tracking_no, shipped_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE carrier = VALUES(carrier), tracking_no = VALUES(tracking_no)
            """,
            (order_id, carrier, tracking),
        )
    return {"id": order_id, "status": "SHIPPED", "carrier": carrier, "tracking_no": tracking}
