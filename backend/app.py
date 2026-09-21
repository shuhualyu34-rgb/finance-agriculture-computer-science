"""丹邱丝苗米普惠产融服务平台 API(阶段 1:鉴权 + 写入闭环)。"""

import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.auth import require_roles
from backend.config import settings
from backend.routers import admin, auth, bank, consumer, farmer, insurance, overview, uploads

app = FastAPI(title="丹邱丝苗米普惠产融服务平台 API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 公开:既有只读接口 + 登录 + 溯源
app.include_router(overview.router)
app.include_router(auth.router)

# 农户端 H5(手机号登录后使用)
app.include_router(farmer.router, dependencies=[Depends(require_roles("FARMER"))])

# 消费端 H5
app.include_router(consumer.router)

# 银行端 / 保险公司端 / 管理后台(对应角色才能访问)
app.include_router(bank.router, dependencies=[Depends(require_roles("BANK", "ADMIN"))])
app.include_router(insurance.router, dependencies=[Depends(require_roles("INSURANCE", "ADMIN"))])
app.include_router(admin.router, dependencies=[Depends(require_roles("OPERATOR", "ADMIN"))])

# 图片上传(登录即可)与静态访问
app.include_router(uploads.router)
_uploads = settings.upload_dir
os.makedirs(_uploads, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads), name="uploads")
