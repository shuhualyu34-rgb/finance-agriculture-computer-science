"""银行端(Web):授信建议列表、农户画像、审批操作(PRD v5 §3.1)。"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.db import query, query_one, transaction
from backend.schemas import BankLoanReview

router = APIRouter(prefix="/api/bank", tags=["bank"])


@router.get("/loans")
def bank_loans(result: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """授信建议列表(需 BANK 角色,守卫在 app.py 全局挂载)。"""
    sql = """
      SELECT l.*, u.real_name AS farmer_name, u.phone AS farmer_phone,
             p.plot_name, p.plot_code, f.certification_status,
             (SELECT COUNT(*) FROM insurance_policy ip
               WHERE ip.farmer_id = l.farmer_id AND ip.status IN ('APPLIED','ACTIVE')) AS policy_count
      FROM loan_application l
      JOIN farmer_profile f ON f.id = l.farmer_id
      JOIN sys_user u ON u.id = f.user_id
      JOIN farm_plot p ON p.id = l.plot_id
    """
    params: tuple[Any, ...] = ()
    if result:
        sql += " WHERE l.bank_result = %s"
        params = (result,)
    sql += " ORDER BY l.applied_at DESC LIMIT 200"
    return query(sql, params)


@router.get("/farmers/{farmer_id}")
def bank_farmer_profile(farmer_id: int) -> dict[str, Any]:
    """农户画像:基本信息 + 认证 + 保险 + 农事记录摘要。"""
    farmer = query_one(
        """
        SELECT f.*, u.real_name, u.phone, u.username
        FROM farmer_profile f JOIN sys_user u ON u.id = f.user_id
        WHERE f.id = %s
        """,
        (farmer_id,),
    )
    if not farmer:
        raise HTTPException(status_code=404, detail="农户不存在")
    farmer["plots"] = query(
        "SELECT id, plot_name, plot_code, area_mu, variety, status FROM farm_plot WHERE farmer_id = %s",
        (farmer_id,),
    )
    farmer["policies"] = query(
        """
        SELECT i.policy_no, i.insured_amount, i.farmer_premium, i.status, i.applied_at
        FROM insurance_policy i WHERE i.farmer_id = %s ORDER BY i.id DESC
        """,
        (farmer_id,),
    )
    farmer["records"] = query(
        """
        SELECT r.record_type, r.record_date, r.description, r.status, p.plot_name
        FROM farm_record r JOIN farm_plot p ON p.id = r.plot_id
        WHERE p.farmer_id = %s ORDER BY r.record_date DESC LIMIT 30
        """,
        (farmer_id,),
    )
    return farmer


@router.put("/loans/{loan_id}/review")
def review_loan(loan_id: int, body: BankLoanReview) -> dict[str, Any]:
    if body.result not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="result 只能是 APPROVED 或 REJECTED")
    loan = query_one("SELECT * FROM loan_application WHERE id = %s", (loan_id,))
    if not loan:
        raise HTTPException(status_code=404, detail="贷款申请不存在")
    if loan["bank_result"] != "PENDING":
        raise HTTPException(status_code=409, detail="该申请已审批过,不能重复操作")
    with transaction() as tx:
        tx["cursor"].execute(
            """
            UPDATE loan_application
            SET bank_result = %s, bank_note = %s, reviewed_at = NOW()
            WHERE id = %s
            """,
            (body.result, body.note or None, loan_id),
        )
    return {"id": loan_id, "bank_result": body.result}
