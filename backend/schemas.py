"""请求体模型(写入接口)。"""

from pydantic import BaseModel, Field


class CaptchaRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11)


class LoginRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11)
    captcha_code: str = Field(min_length=1, max_length=8)


class FarmRecordCreate(BaseModel):
    plot_id: int
    record_type: str  # SOWING/FERTILIZING/PESTICIDE/IRRIGATION/HARVEST/QUALITY_TEST
    record_date: str  # YYYY-MM-DD
    description: str = ""
    material_name: str | None = None
    material_amount: float | None = None
    output_jin: float | None = None
    photo_urls: list[str] = []


class CertificationCreate(BaseModel):
    plot_id: int
    note: str = ""


class InsuranceApply(BaseModel):
    plot_id: int
    product_id: int = 1


class LoanApply(BaseModel):
    plot_id: int
    purpose_note: str = ""


class AdoptionCreate(BaseModel):
    plot_id: int


class BankLoanReview(BaseModel):
    result: str  # APPROVED / REJECTED
    note: str = ""


class ClaimCreate(BaseModel):
    policy_id: int
    disaster_note: str
    disaster_rate: float = Field(ge=0, le=1)


class ClaimReview(BaseModel):
    status: str  # APPROVED / REJECTED / PAID
