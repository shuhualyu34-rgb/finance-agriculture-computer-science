"""阶段 1 写入闭环集成测试:认证 → 农事上传 → 认证/保险/贷款 → 银行审批 → 理赔 → 分红。

需要 Docker 栈运行中(docker-compose up -d);种子数据账号:
  农户1 黄强 13800015892 / 消费者 张玲 13900015066 / 银行 13764807553
  保险 13753091709 / 管理员 13765250068
"""

import os

import httpx
import pytest

BASE = os.getenv("DANQIU_API_BASE", "http://127.0.0.1:8010")
CAPTCHA = "1234"  # PRD v5 §八:本期验证码写死

FARMER_PHONE = os.getenv("TEST_FARMER_PHONE", "13800015892")
CONSUMER_PHONE = os.getenv("TEST_CONSUMER_PHONE", "13900015066")
BANK_PHONE = os.getenv("TEST_BANK_PHONE", "13764807553")
INSURANCE_PHONE = os.getenv("TEST_INSURANCE_PHONE", "13753091709")
ADMIN_PHONE = os.getenv("TEST_ADMIN_PHONE", "13765250068")


def _available() -> bool:
    try:
        return httpx.get(f"{BASE}/api/health", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _available(), reason=f"API 未启动({BASE})")


def login(phone: str) -> dict:
    r = httpx.post(f"{BASE}/api/auth/login", json={"phone": phone, "captcha_code": CAPTCHA}, timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["phone"] == phone
    return body


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def farmer() -> dict:
    return login(FARMER_PHONE)


@pytest.fixture(scope="module")
def consumer() -> dict:
    return login(CONSUMER_PHONE)


def test_login_captcha_wrong():
    r = httpx.post(
        f"{BASE}/api/auth/login",
        json={"phone": FARMER_PHONE, "captcha_code": "0000"},
        timeout=5,
    )
    assert r.status_code == 400


def test_me(farmer):
    r = httpx.get(f"{BASE}/api/auth/me", headers=auth(farmer["access_token"]), timeout=5)
    assert r.status_code == 200
    assert "FARMER" in r.json()["roles"]


def test_farmer_rbac_blocks_bank(farmer):
    r = httpx.get(f"{BASE}/api/bank/loans", headers=auth(farmer["access_token"]), timeout=5)
    assert r.status_code == 403


def test_farmer_summary_and_plots(farmer):
    token = auth(farmer["access_token"])
    summary = httpx.get(f"{BASE}/api/my/summary", headers=token, timeout=5).json()
    assert summary["farmer"]["id"] >= 1
    plots = httpx.get(f"{BASE}/api/my/plots", headers=token, timeout=5).json()
    assert plots, "种子农户应至少有一块地"
    assert {"id", "plot_name", "area_mu", "cert_status"} <= set(plots[0])


def test_upload_and_create_record(farmer):
    token = auth(farmer["access_token"])
    # 1x1 红色 PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8cfc00000030101"
        "00c9fe92ef0000000049454e44ae426082"
    )
    up = httpx.post(f"{BASE}/api/uploads", headers=token, files={"file": ("photo.png", png, "image/png")}, timeout=5)
    assert up.status_code == 200, up.text
    url = up.json()["url"]
    assert url.startswith("/uploads/")

    plots = httpx.get(f"{BASE}/api/my/plots", headers=token, timeout=5).json()
    plot_id = plots[0]["id"]
    today = "2026-09-21"
    r = httpx.post(
        f"{BASE}/api/my/records",
        headers=token,
        json={
            "plot_id": plot_id,
            "record_type": "FERTILIZING",
            "record_date": today,
            "description": "集成测试:施有机肥",
            "material_name": "有机肥",
            "material_amount": 50,
            "photo_urls": [url],
        },
        timeout=5,
    )
    assert r.status_code == 201, r.text
    rec_id = r.json()["id"]
    records = httpx.get(f"{BASE}/api/my/records", headers=token, params={"plot_id": plot_id}, timeout=5).json()
    mine = [x for x in records if x["id"] == rec_id]
    assert mine and mine[0]["description"] == "集成测试:施有机肥"
    assert url in (mine[0]["photo_urls"] or "")


def test_record_validation(farmer):
    token = auth(farmer["access_token"])
    plots = httpx.get(f"{BASE}/api/my/plots", headers=token, timeout=5).json()
    r = httpx.post(
        f"{BASE}/api/my/records",
        headers=token,
        json={"plot_id": plots[0]["id"], "record_type": "NOT_A_TYPE", "record_date": "2026-09-21"},
        timeout=5,
    )
    assert r.status_code == 400
    r = httpx.post(
        f"{BASE}/api/my/records",
        headers=token,
        json={"plot_id": plots[0]["id"], "record_type": "SOWING", "record_date": "2099-01-01"},
        timeout=5,
    )
    assert r.status_code == 400


def test_certification_apply(farmer):
    token = auth(farmer["access_token"])
    plots = httpx.get(f"{BASE}/api/my/plots", headers=token, timeout=5).json()
    # 找一块没有待审申请的地
    for plot in plots:
        r = httpx.post(f"{BASE}/api/my/certifications", headers=token, json={"plot_id": plot["id"], "note": "集成测试申请"}, timeout=5)
        if r.status_code == 201:
            body = r.json()
            assert body["status"] == "PENDING"
            dup = httpx.post(f"{BASE}/api/my/certifications", headers=token, json={"plot_id": plot["id"]}, timeout=5)
            assert dup.status_code == 409
            return
    pytest.skip("该农户所有地块均已有待审申请")


def test_insurance_quote_and_apply(farmer):
    token = auth(farmer["access_token"])
    plots = httpx.get(f"{BASE}/api/my/plots", headers=token, timeout=5).json()
    area = float(plots[0]["area_mu"])
    r = httpx.post(f"{BASE}/api/my/insurance", headers=token, json={"plot_id": plots[0]["id"], "product_id": 1}, timeout=5)
    assert r.status_code == 201, r.text
    quote = r.json()["quote"]
    # PRD:保额=面积×1500;总保费=保额×5%;农户自缴=总保费×20%
    assert quote["insured_amount"] == round(area * 1500, 2)
    assert quote["total_premium"] == round(quote["insured_amount"] * 0.05, 2)
    assert quote["farmer_premium"] == round(quote["total_premium"] * 0.20, 2)
    policies = httpx.get(f"{BASE}/api/my/policies", headers=token, timeout=5).json()
    assert any(p["insured_amount"] == quote["insured_amount"] for p in policies)


def test_loan_apply_and_bank_review(farmer):
    token = auth(farmer["access_token"])
    plots = httpx.get(f"{BASE}/api/my/plots", headers=token, timeout=5).json()
    area = float(plots[0]["area_mu"])
    r = httpx.post(f"{BASE}/api/my/loans", headers=token, json={"plot_id": plots[0]["id"]}, timeout=5)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["suggested_amount"] == round(area * 800, 2)  # PRD:建议额度=面积×800
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    loan_id = body["id"]

    bank = login(BANK_PHONE)
    pending = httpx.get(f"{BASE}/api/bank/loans", headers=auth(bank["access_token"]), params={"result": "PENDING"}, timeout=5).json()
    assert any(x["id"] == loan_id for x in pending)
    rv = httpx.put(
        f"{BASE}/api/bank/loans/{loan_id}/review",
        headers=auth(bank["access_token"]),
        json={"result": "APPROVED", "note": "集成测试放款"},
        timeout=5,
    )
    assert rv.status_code == 200
    again = httpx.put(
        f"{BASE}/api/bank/loans/{loan_id}/review",
        headers=auth(bank["access_token"]),
        json={"result": "REJECTED"},
        timeout=5,
    )
    assert again.status_code == 409  # 不能重复审批
    mine = httpx.get(f"{BASE}/api/my/loans", headers=token, timeout=5).json()
    assert any(x["id"] == loan_id and x["bank_result"] == "APPROVED" for x in mine)


def test_claim_flow(farmer):
    token = auth(farmer["access_token"])
    policies = httpx.get(f"{BASE}/api/my/policies", headers=token, timeout=5).json()
    assert policies, "前置:农户应已有保单"
    policy = policies[0]

    staff = login(INSURANCE_PHONE)
    r = httpx.post(
        f"{BASE}/api/insurance/claims",
        headers=auth(staff["access_token"]),
        json={"policy_id": policy["id"], "disaster_note": "台风倒伏(集成测试)", "disaster_rate": 0.3},
        timeout=5,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    # PRD:赔付 = 保额 × 受灾比例
    assert body["claim_amount"] == round(float(policy["insured_amount"]) * 0.3, 2)
    claim_id = body["id"]

    rv = httpx.put(
        f"{BASE}/api/insurance/claims/{claim_id}/review",
        headers=auth(staff["access_token"]),
        json={"status": "APPROVED"},
        timeout=5,
    )
    assert rv.status_code == 200
    mine = httpx.get(f"{BASE}/api/my/claims", headers=token, timeout=5).json()
    assert any(x["id"] == claim_id and x["status"] == "APPROVED" for x in mine)


def test_consumer_adoption(consumer):
    token = auth(consumer["access_token"])
    plots = httpx.get(f"{BASE}/api/adoption/plots", headers=token, timeout=5).json()
    assert plots, "应有开放认养的地块"
    target = next((p for p in plots if not p["adopted_count"]), plots[0])
    r = httpx.post(f"{BASE}/api/adoption/orders", headers=token, json={"plot_id": target["id"]}, timeout=5)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "PAID"  # Demo 模拟支付
    dup = httpx.post(f"{BASE}/api/adoption/orders", headers=token, json={"plot_id": target["id"]}, timeout=5)
    assert dup.status_code == 409


def test_admin_dividends_and_cert_review(farmer):
    admin = login(ADMIN_PHONE)
    token = auth(admin["access_token"])
    r = httpx.post(f"{BASE}/api/admin/dividends/calculate", headers=token, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["dividend_rate"] == 0.05
    # 再次计算应幂等(无新增)
    r2 = httpx.post(f"{BASE}/api/admin/dividends/calculate", headers=token, timeout=10)
    assert r2.json()["dividends_created"] == 0

    pending = httpx.get(f"{BASE}/api/admin/certifications", headers=token, timeout=5).json()
    assert isinstance(pending, list)
