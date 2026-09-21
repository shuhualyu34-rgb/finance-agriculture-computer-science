"""文件上传:农事照片、检测报告(PRD v5 §4.1 拍照+文字记录)。"""

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile

from backend.auth import CurrentUser
from backend.config import settings

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("")
def upload_image(user: CurrentUser, file: UploadFile) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"仅支持图片格式: {sorted(ALLOWED_EXTENSIONS)}")
    data = file.file.read()
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 10MB")
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    (upload_dir / name).write_bytes(data)
    return {"url": f"/uploads/{name}", "size": len(data), "content_type": file.content_type}
