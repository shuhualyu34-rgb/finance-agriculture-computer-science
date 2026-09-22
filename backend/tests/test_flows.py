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
        payload = {"plot_id": plot["id"], "note": "集成测试申请"}
        r = httpx.post(f"{BASE}/api/my/certifications", headers=token, json=payload, timeout=5)
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
    payload = {"plot_id": plots[0]["id"], "product_id": 1}
    r = httpx.post(f"{BASE}/api/my/insurance", headers=token, json=payload, timeout=5)
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
    bank_headers = auth(bank["access_token"])
    pending = httpx.get(
        f"{BASE}/api/bank/loans", headers=bank_headers, params={"result": "PENDING"}, timeout=5
    ).json()
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
    # 我的认养列表应包含刚下的单
    mine = httpx.get(f"{BASE}/api/my/adoptions", headers=token, timeout=5).json()
    adopted = [x for x in mine if x["plot_name"] == target["plot_name"]]
    assert adopted and adopted[0]["status"] == "PAID"
    assert {"order_no", "fee", "farmer_name", "updates_since_adopted"} <= set(adopted[0])


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


def test_government_dashboard_public():
    r = httpx.get(f"{BASE}/api/government/dashboard", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert {"cards", "map", "dynamics"} <= set(body)
    assert body["cards"]["total_farmers"] >= 200
    assert body["map"]["plots"], "地图应包含地块边界"
    assert body["dynamics"], "应有最新业务动态"


def test_operator_standards_and_trace_codes(farmer):
    operator = login("13799943797")  # 品牌运营专员
    token = auth(operator["access_token"])

    standards = httpx.get(f"{BASE}/api/operator/standards", headers=token, timeout=5).json()
    assert standards, "应已有标准版本"
    assert standards[0]["clauses"], "标准版本应含条款"

    r = httpx.post(
        f"{BASE}/api/operator/trace-codes",
        headers=token,
        json={"plot_id": 1, "batch_name": "集成测试批次", "product_grade": "FIRST"},
        timeout=5,
    )
    assert r.status_code == 201, r.text
    code = r.json()["code"]
    assert len(code) == 16
    trace = httpx.get(f"{BASE}/api/trace/{code}", timeout=5)
    assert trace.status_code == 200
    tid = r.json()["id"]
    rv = httpx.put(f"{BASE}/api/operator/trace-codes/{tid}/disable", headers=token, timeout=5)
    assert rv.status_code == 200
    trace2 = httpx.get(f"{BASE}/api/trace/{code}", timeout=5)
    assert trace2.status_code == 404
    r2 = httpx.get(f"{BASE}/api/operator/standards", headers=auth(farmer["access_token"]), timeout=5)
    assert r2.status_code == 403


def test_admin_users_plots_and_config():
    admin = login(ADMIN_PHONE)
    token = auth(admin["access_token"])

    users = httpx.get(f"{BASE}/api/admin/users", headers=token, params={"role": "FARMER"}, timeout=5).json()
    assert len(users) >= 200

    plots = httpx.get(f"{BASE}/api/admin/plots", headers=token, timeout=5).json()
    assert plots, "应有地块"
    target = next(p for p in plots if p["open_for_adoption"] == 0)
    rv = httpx.put(
        f"{BASE}/api/admin/plots/{target['id']}/adoption", headers=token, json={"open": True}, timeout=5
    )
    assert rv.status_code == 200 and rv.json()["open_for_adoption"] is True
    back = httpx.put(
        f"{BASE}/api/admin/plots/{target['id']}/adoption", headers=token, json={"open": False}, timeout=5
    )
    assert back.status_code == 200

    products = httpx.get(f"{BASE}/api/admin/insurance-products", headers=token, timeout=5).json()
    assert products, "应有保险产品"
    p1 = products[0]
    upd = httpx.put(
        f"{BASE}/api/admin/insurance-products/{p1['id']}",
        headers=token,
        json={
            "insured_amount_per_mu": float(p1["insured_amount_per_mu"]),
            "premium_rate": float(p1["premium_rate"]),
            "government_subsidy_rate": float(p1["government_subsidy_rate"]),
        },
        timeout=5,
    )
    assert upd.status_code == 200


def test_mall_full_loop_to_dividend(consumer):
    """PRD §12:消费者下单 -> 模拟支付 -> 运营发货 -> 确认收货 -> 农户分红。"""
    token = auth(consumer["access_token"])

    products = httpx.get(f"{BASE}/api/shop/products", timeout=5).json()
    assert products, "商城应有在售商品"
    product = next((p for p in products if p["stock"] >= 2), products[0])
    qty = 2 if product["stock"] >= 2 else 1

    r = httpx.post(
        f"{BASE}/api/shop/orders",
        headers=token,
        json={
            "items": [{"product_id": product["id"], "quantity": qty}],
            "receiver": "张玲",
            "phone": CONSUMER_PHONE,
            "detail_address": "广州市增城区朱村街道测试地址 8 栋",
        },
        timeout=5,
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "PENDING_PAYMENT"
    assert order["total_amount"] == round(float(product["price"]) * qty, 2)
    order_id = order["id"]

    early = httpx.post(f"{BASE}/api/shop/orders/{order_id}/confirm", headers=token, timeout=5)
    assert early.status_code == 409

    pay = httpx.post(f"{BASE}/api/shop/orders/{order_id}/pay", headers=token, timeout=5)
    assert pay.status_code == 200 and pay.json()["status"] == "PAID"

    mine = httpx.get(f"{BASE}/api/shop/my-orders", headers=token, timeout=5).json()
    target = next(o for o in mine if o["id"] == order_id)
    assert target["items"][0]["product_name"] == product["product_name"]

    operator = login("13799943797")
    ot = auth(operator["access_token"])
    r = httpx.put(
        f"{BASE}/api/shop/orders/{order_id}/ship",
        headers=ot,
        json={"carrier": "顺丰速运", "tracking_no": "SF1234567890"},
        timeout=5,
    )
    assert r.status_code == 200, r.text
    ops_orders = httpx.get(
        f"{BASE}/api/shop/orders", headers=ot, params={"status": "SHIPPED"}, timeout=5
    ).json()
    assert any(o["id"] == order_id and o["tracking_no"] == "SF1234567890" for o in ops_orders)

    confirm = httpx.post(f"{BASE}/api/shop/orders/{order_id}/confirm", headers=token, timeout=5)
    assert confirm.status_code == 200 and confirm.json()["status"] == "COMPLETED"

    admin = login(ADMIN_PHONE)
    calc = httpx.post(f"{BASE}/api/admin/dividends/calculate", headers=auth(admin["access_token"]), timeout=10)
    assert calc.status_code == 200
    body = calc.json()
    assert body["dividends_created"] >= 1, "新完成订单应计提分红"
    assert body["total_dividend_amount"] > 0
    calc2 = httpx.post(f"{BASE}/api/admin/dividends/calculate", headers=auth(admin["access_token"]), timeout=10)
    assert calc2.json()["dividends_created"] == 0


def test_government_reports_and_inspections():
    gov = login("13731585546")  # 农业局监管员
    token = auth(gov["access_token"])

    # 生成周报/月报(幂等)
    r = httpx.post(f"{BASE}/api/government/reports/generate", headers=token,
                   json={"report_type": "WEEKLY"}, timeout=10)
    assert r.status_code == 201, r.text
    weekly = r.json()
    assert weekly["report_period"].count("-W") == 1
    again = httpx.post(f"{BASE}/api/government/reports/generate", headers=token,
                       json={"report_type": "WEEKLY"}, timeout=10)
    assert again.json()["id"] == weekly["id"] and again.json()["created"] is False

    monthly = httpx.post(f"{BASE}/api/government/reports/generate", headers=token,
                         json={"report_type": "MONTHLY"}, timeout=10).json()

    # 详情内容结构
    detail = httpx.get(f"{BASE}/api/government/reports/{monthly['id']}", headers=token, timeout=5).json()
    assert {"farmers", "production", "inspections", "insurance", "loans", "sales"} <= set(detail["content"])

    # 确认(含现场备注)
    rv = httpx.put(f"{BASE}/api/government/reports/{monthly['id']}/confirm", headers=token,
                   json={"note": "现场抽查无异常"}, timeout=5)
    assert rv.status_code == 200
    d2 = httpx.get(f"{BASE}/api/government/reports/{monthly['id']}", headers=token, timeout=5).json()
    assert d2["status"] == "CONFIRMED" and d2["content"]["site_note"] == "现场抽查无异常"

    # 留档列表
    reports = httpx.get(f"{BASE}/api/government/reports", headers=token, timeout=5).json()
    assert any(x["id"] == monthly["id"] for x in reports)

    # 实地采集:面积差异 >20% 自动预警
    insp = httpx.post(f"{BASE}/api/government/inspections", headers=token, json={
        "plot_id": 1, "inspection_date": "2026-09-21", "result": "PASS",
        "actual_area_mu": 0.5,
    }, timeout=5)
    assert insp.status_code == 201, insp.text
    body = insp.json()
    assert body["auto_warning"] is True and body["result"] == "WARNING"
    assert "面积交叉核验" in body["note"]
    listing = httpx.get(f"{BASE}/api/government/inspections", headers=token, timeout=5).json()
    assert any(x["id"] == body["id"] for x in listing)

    # 农户角色不能访问
    farmer_token = auth(login(FARMER_PHONE)["access_token"])
    r403 = httpx.get(f"{BASE}/api/government/reports", headers=farmer_token, timeout=5)
    assert r403.status_code == 403


def test_farmer_income(farmer):
    token = auth(farmer["access_token"])
    r = httpx.get(f"{BASE}/api/my/income", headers=token, timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert {"RENT", "WAGE", "BRAND_PREMIUM", "DIVIDEND", "TOTAL"} <= set(body["summary"])
    assert body["summary"]["RENT"] > 0
    assert body["summary"]["WAGE"] > 0
    assert isinstance(body["items"], list)



