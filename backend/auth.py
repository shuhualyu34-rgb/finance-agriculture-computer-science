"""鉴权:手机号 + 固定验证码登录(PRD v5 §八:验证码写死 1234),JWT Bearer。"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import settings
from backend.db import query

bearer_scheme = HTTPBearer(auto_error=False)


def create_token(user_id: int, roles: list[str]) -> str:
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "exp": datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="登录已过期,请重新登录") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="无效的登录凭证") from exc


def load_user(user_id: int) -> dict[str, Any]:
    """用户 + 角色,不存在返回 None。"""
    user = query(
        """
        SELECT u.id, u.username, u.real_name, u.phone, u.status
        FROM sys_user u WHERE u.id = %s
        """,
        (user_id,),
    )
    if not user or user[0]["status"] != "ACTIVE":
        return None
    roles = query(
        """
        SELECT r.role_code FROM sys_role r
        JOIN sys_user_role ur ON ur.role_id = r.id
        WHERE ur.user_id = %s ORDER BY r.id
        """,
        (user_id,),
    )
    result = user[0]
    result["roles"] = [row["role_code"] for row in roles]
    return result


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="请先登录")
    payload = decode_token(credentials.credentials)
    user = load_user(int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="账号不存在或已停用")
    return user


def require_roles(*required: str):
    """角色守卫工厂:require_roles('FARMER') 生成依赖。"""

    def checker(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        if not set(user["roles"]) & set(required):
            raise HTTPException(status_code=403, detail=f"需要角色: {'/'.join(required)}")
        return user

    return checker


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
