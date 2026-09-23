"""保险公司端(Web)+ 管理员理赔录入(PRD v5 §3.2)。

角色守卫(INSURANCE/ADMIN)在 app.py 挂载路由时统一施加。
"""

import json
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response

from backend.auth import CurrentUser
from backend.db import query, query_one, transaction
from backend.rules import claim_amount, weather_index_assessment
from backend.schemas import ClaimCreate, ClaimReview, WeatherAssessCreate

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


def claim_no(prefix: str) -> str:
    """理赔单号:日期 + 8 位十六进制随机后缀,避免同日并发撞 UNIQUE 约束。"""
    return f"{prefix}{date.today().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


@router.get("/products")
def insurance_products() -> list[dict[str, Any]]:
    """保险产品矩阵；当前为平台配置/演示产品，不代表真实承保。"""
    return query(
        "SELECT id, product_code, product_type, product_name, insured_amount_per_mu, premium_rate, "
        "government_subsidy_rate, trigger_config, description FROM insurance_product "
        "WHERE status = 'ACTIVE' ORDER BY id"
    )


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
    no = claim_no("CL")
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO insurance_claim
              (claim_no, policy_id, disaster_note, disaster_rate, claim_amount, assessment_mode,
               assessment_json, entered_by, status)
            VALUES (%s, %s, %s, %s, %s, 'MANUAL', %s, %s, 'SUBMITTED')
            """,
            (no, policy["id"], body.disaster_note, body.disaster_rate, amount,
             json.dumps({"source": "MANUAL", "loss_rate": body.disaster_rate}, ensure_ascii=False), user["id"]),
        )
        claim_id = cursor.lastrowid
    return {"id": claim_id, "claim_no": no, "claim_amount": amount, "status": "SUBMITTED"}


@router.post("/weather-index/assess")
def assess_weather_index(user: CurrentUser, response: Response, body: WeatherAssessCreate) -> dict[str, Any]:
    """用气象数据生成气象指数定损草案，达到阈值后仍需人工复核。

    状态码语义:仅实际生成理赔草案时返回 201;未达触发阈值返回 200。
    幂等:同一保单存在待复核(SUBMITTED)的气象指数草案时拒绝重复生成。
    """
    policy = query_one(
        """SELECT i.*, p.product_type, p.product_code, p.product_name, p.trigger_config
           FROM insurance_policy i JOIN insurance_product p ON p.id = i.product_id
           WHERE i.id = %s AND i.status IN ('APPLIED','ACTIVE')""",
        (body.policy_id,),
    )
    if not policy:
        raise HTTPException(status_code=404, detail="保单不存在或不在保障期")
    if policy["product_type"] != "WEATHER_INDEX":
        raise HTTPException(status_code=400, detail="该保单不是气象指数保险")
    assessment = weather_index_assessment(
        float(policy["insured_amount"]), policy["trigger_config"],
        body.wind_speed_kmh, body.rainfall_mm,
    )
    if not assessment["triggered"]:
        return {"triggered": False, "assessment": assessment, "note": "未达到触发阈值，不生成理赔草案"}
    existing = query_one(
        "SELECT claim_no FROM insurance_claim "
        "WHERE policy_id = %s AND assessment_mode = 'WEATHER_INDEX' AND status = 'SUBMITTED'",
        (policy["id"],),
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"该保单已存在待复核的气象指数定损草案({existing['claim_no']})，请先完成复核",
        )
    no = claim_no("WX")
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """INSERT INTO insurance_claim
              (claim_no, policy_id, disaster_note, disaster_rate, claim_amount, assessment_mode,
               assessment_json, entered_by, status)
              VALUES (%s, %s, %s, %s, %s, 'WEATHER_INDEX', %s, %s, 'SUBMITTED')""",
            (no, policy["id"], body.note or "气象指数触发的自动定损草案",
             assessment["loss_rate"], assessment["claim_amount"],
             json.dumps(assessment, ensure_ascii=False), user["id"]),
        )
        claim_id = cursor.lastrowid
    response.status_code = 201
    return {"id": claim_id, "claim_no": no, "status": "SUBMITTED", "assessment": assessment,
            "note": "已生成定损草案，需保险人员复核后赔付"}


@router.get("/claims")
def insurance_claims(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """理赔台账。"""
    sql = """
      SELECT c.*, i.policy_no, i.insured_amount, pr.product_code, pr.product_type,
             pr.product_name, u.real_name AS farmer_name, p.plot_name
      FROM insurance_claim c
      JOIN insurance_policy i ON i.id = c.policy_id
      JOIN insurance_product pr ON pr.id = i.product_id
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
