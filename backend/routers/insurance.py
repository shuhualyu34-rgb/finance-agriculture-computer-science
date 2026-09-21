"""保险公司端(Web)+ 管理员理赔录入(PRD v5 §3.2)。"""

import random
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.auth import CurrentUser
from backend.db import query, query_one, transaction
from backend.rules import claim_amount
from backend.schemas import ClaimCreate, ClaimReview

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


@router.get("/policies")
def insurance_policies(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """保单管理列表。"""
    sql = """
      SELECT i.*, u.real_name AS farmer_name, u.phone AS farmer_phone,
             p.plot_name, pr.product_name
      FROM insurance_policy i
      JOIN farmer_profile f ON f.id = i.farmer_id
      JOIN sys_user u ON u.id = f.user_id
      JOIN farm_plot p ON p.id = i.plot_id
      JOIN insurance_product pr ON pr.id = i.product_id
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE i.status = %s"
        params = (status,)
    sql += " ORDER BY i.applied_at DESC LIMIT 200"
    return query(sql, params)


@router.post("/claims", status_code=201)
def create_claim(user: CurrentUser, body: ClaimCreate) -> dict[str, Any]:
    """管理员/保险公司录入受灾情况,系统自动算赔付(赔付 = 保额 × 受灾比例)。"""
    policy = query_one(
        """
        SELECT i.*, f.id AS farmer_id FROM insurance_policy i
        JOIN farmer_profile f ON f.id = i.farmer_id
        WHERE i.id = %s AND i.status IN ('APPLIED','ACTIVE')
        """,
        (body.policy_id,),
    )
    if not policy:
        raise HTTPException(status_code=404, detail="保单不存在或不在保障期")
    amount = claim_amount(float(policy["insured_amount"]), body.disaster_rate)
    claim_no = f"CL{date.today().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO insurance_claim
              (claim_no, policy_id, disaster_note, disaster_rate, claim_amount, entered_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'SUBMITTED')
            """,
            (claim_no, policy["id"], body.disaster_note, body.disaster_rate, amount, user["id"]),
        )
        claim_id = cursor.lastrowid
    return {"id": claim_id, "claim_no": claim_no, "claim_amount": amount, "status": "SUBMITTED"}


@router.get("/claims")
def insurance_claims(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """理赔台账。"""
    sql = """
      SELECT c.*, i.policy_no, i.insured_amount, u.real_name AS farmer_name, p.plot_name
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
    sql += " ORDER BY c.id DESC LIMIT 200"
    return query(sql, params)


@router.put("/claims/{claim_id}/review")
def review_claim(claim_id: int, user: CurrentUser, body: ClaimReview) -> dict[str, Any]:
    """保险公司复核:APPROVED / REJECTED / PAID。"""
    if body.status not in ("APPROVED", "REJECTED", "PAID"):
        raise HTTPException(status_code=400, detail="status 只能是 APPROVED、REJECTED 或 PAID")
    claim = query_one("SELECT * FROM insurance_claim WHERE id = %s", (claim_id,))
    if not claim:
        raise HTTPException(status_code=404, detail="理赔记录不存在")
    if claim["status"] in ("PAID", "REJECTED"):
        raise HTTPException(status_code=409, detail="该理赔已终审,不能重复操作")
    with transaction() as tx:
        tx["cursor"].execute(
            """
            UPDATE insurance_claim SET status = %s, reviewed_by = %s, reviewed_at = NOW()
            WHERE id = %s
            """,
            (body.status, user["id"], claim_id),
        )
    return {"id": claim_id, "status": body.status}
