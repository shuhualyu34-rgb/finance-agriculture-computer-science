"""品牌运营端(PRD v5 §4.5):标准管理、认证审批(见 admin.py)、溯源码管理。"""

import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.auth import CurrentUser
from backend.db import query, query_one, transaction

router = APIRouter(prefix="/api/operator", tags=["operator"])


@router.get("/standards")
def standards() -> list[dict[str, Any]]:
    """标准库:版本 + 按环节分组的条款(PRD §10 六大环节)。"""
    versions = query("SELECT * FROM standard_version ORDER BY id DESC")
    stage_order = ["PLANTING", "PROCESSING", "QUALITY", "GRADING", "PACKAGING", "DISTRIBUTION"]
    for v in versions:
        clauses = query(
            "SELECT * FROM standard_clause WHERE standard_id = %s",
            (v["id"],),
        )
        clauses.sort(key=lambda c: stage_order.index(c["stage"]) if c["stage"] in stage_order else 99)
        v["clauses"] = clauses
    return versions


@router.get("/trace-codes")
def trace_codes(status: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """溯源码管理:一批一码列表。"""
    sql = """
      SELECT t.*, p.plot_name, p.plot_code, s.season_name
      FROM trace_code t
      JOIN farm_plot p ON p.id = t.plot_id
      JOIN production_season s ON s.id = t.season_id
    """
    params: tuple[Any, ...] = ()
    if status:
        sql += " WHERE t.status = %s"
        params = (status,)
    sql += " ORDER BY t.id DESC LIMIT 200"
    return query(sql, params)


@router.post("/trace-codes", status_code=201)
def create_trace_code(user: CurrentUser, body: dict[str, Any]) -> dict[str, Any]:
    """生成溯源码并绑定地块批次。body: {plot_id, batch_name, product_grade}"""
    plot = query_one(
        "SELECT * FROM farm_plot WHERE id = %s AND status = 'ACTIVE'", (body.get("plot_id"),)
    )
    if not plot:
        raise HTTPException(status_code=404, detail="地块不存在")
    grade = body.get("product_grade", "FIRST")
    if grade not in ("SPECIAL", "FIRST", "SECOND"):
        raise HTTPException(status_code=400, detail="product_grade 只能是 SPECIAL/FIRST/SECOND")
    season = query_one(
        "SELECT * FROM production_season WHERE status IN ('IN_PROGRESS','HARVESTED') ORDER BY id DESC LIMIT 1"
    )
    if not season:
        raise HTTPException(status_code=503, detail="系统缺少种植季数据")
    code = secrets.token_hex(8).upper()
    with transaction() as tx:
        cursor = tx["cursor"]
        cursor.execute(
            """
            INSERT INTO trace_code (code, plot_id, season_id, batch_name, product_grade, status)
            VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
            """,
            (code, plot["id"], season["id"], body.get("batch_name") or f"{plot['plot_name']} 批次", grade),
        )
        trace_id = cursor.lastrowid
    return {"id": trace_id, "code": code, "status": "ACTIVE"}


@router.put("/trace-codes/{trace_id}/disable")
def disable_trace_code(user: CurrentUser, trace_id: int) -> dict[str, Any]:
    row = query_one("SELECT * FROM trace_code WHERE id = %s", (trace_id,))
    if not row:
        raise HTTPException(status_code=404, detail="溯源码不存在")
    if row["status"] == "DISABLED":
        raise HTTPException(status_code=409, detail="该溯源码已停用")
    with transaction() as tx:
        tx["cursor"].execute("UPDATE trace_code SET status = 'DISABLED' WHERE id = %s", (trace_id,))
    return {"id": trace_id, "status": "DISABLED"}
