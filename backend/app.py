"""丹邱丝苗米普惠产融服务平台 API(阶段 2:七端全通)。"""

import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.auth import require_roles
from backend.config import settings
from backend.routers import (
    admin,
    auth,
    bank,
    consumer,
    farmer,
    government,
    insurance,
    operator,
    overview,
    uploads,
)

app = FastAPI(title="丹邱丝苗米普惠产融服务平台 API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 公开:只读总览 + 登录 + 溯源 + 政府大屏(展厅公开展示)
app.include_router(overview.router)
app.include_router(auth.router)
app.include_router(government.router)

# 农户端 H5
app.include_router(farmer.router, dependencies=[Depends(require_roles("FARMER"))])

# 消费端 H5
app.include_router(consumer.router)

# 银行端 / 保险公司端
app.include_router(bank.router, dependencies=[Depends(require_roles("BANK", "ADMIN"))])
app.include_router(insurance.router, dependencies=[Depends(require_roles("INSURANCE", "ADMIN"))])

# 品牌运营端(标准/溯源码/认证审批)
app.include_router(operator.router, dependencies=[Depends(require_roles("OPERATOR", "ADMIN"))])
app.include_router(admin.router, dependencies=[Depends(require_roles("OPERATOR", "ADMIN"))])

# 图片上传(登录即可)与静态访问
app.include_router(uploads.router)
_uploads = settings.upload_dir
os.makedirs(_uploads, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads), name="uploads")

# 政府监管大屏静态页(若有)
_bigscreen = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bigscreen")
if os.path.isdir(_bigscreen):
    app.mount("/bigscreen", StaticFiles(directory=_bigscreen, html=True), name="bigscreen")
