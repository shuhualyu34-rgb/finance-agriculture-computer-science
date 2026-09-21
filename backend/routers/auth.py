"""认证:获取验证码、登录、当前用户。"""

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.auth import CurrentUser, create_token, load_user
from backend.config import settings
from backend.db import query
from backend.schemas import CaptchaRequest, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/captcha")
def captcha(body: CaptchaRequest) -> dict[str, Any]:
    """获取短信验证码。PRD v5 §八:本期验证码写死 1234,不接真实短信。"""
    user = query("SELECT id FROM sys_user WHERE phone = %s AND status = 'ACTIVE'", (body.phone,))
    if not user:
        raise HTTPException(status_code=404, detail="该手机号未注册")
    # 开发期直接返回固定验证码,生产环境应替换为短信通道
    return {"phone": body.phone, "captcha": settings.fixed_captcha, "expires_in": 300, "dev_mode": True}


@router.post("/login")
def login(body: LoginRequest) -> dict[str, Any]:
    if body.captcha_code != settings.fixed_captcha:
        raise HTTPException(status_code=400, detail="验证码错误")
    rows = query("SELECT id FROM sys_user WHERE phone = %s AND status = 'ACTIVE'", (body.phone,))
    if not rows:
        raise HTTPException(status_code=404, detail="该手机号未注册")
    user = load_user(rows[0]["id"])
    return {
        "access_token": create_token(user["id"], user["roles"]),
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me")
def me(user: CurrentUser) -> dict[str, Any]:
    return user
