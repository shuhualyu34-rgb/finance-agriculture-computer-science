"""环境变量配置。"""

import os

import pymysql


class Settings:
    """集中读取环境变量,容器与本地开发共用。"""

    db_host: str = os.getenv("DANQIU_DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DANQIU_DB_PORT", "3306"))
    db_user: str = os.getenv("DANQIU_DB_USER", "root")
    db_password: str = os.getenv("DANQIU_DB_PASSWORD", "")
    db_name: str = os.getenv("DANQIU_DB_NAME", "danqiu_rice")

    jwt_secret: str = os.getenv("DANQIU_JWT_SECRET", "danqiu-dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = int(os.getenv("DANQIU_JWT_EXPIRE_HOURS", "168"))

    upload_dir: str = os.getenv("DANQIU_UPLOAD_DIR", "/app/uploads")
    # PRD v5 §八:本期验证码写死 1234
    fixed_captcha: str = "1234"


settings = Settings()

DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name,
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}
