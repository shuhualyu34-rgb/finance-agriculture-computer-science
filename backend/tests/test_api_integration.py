"""集成测试:访问运行中的 API(默认 http://127.0.0.1:8010)。

需要先启动 Docker 组合:docker-compose up -d
未检测到服务时自动跳过,不影响单元测试。
"""

import os

import httpx
import pytest

BASE = os.getenv("DANQIU_API_BASE", "http://127.0.0.1:8010")


def _available() -> bool:
    try:
        return httpx.get(f"{BASE}/api/health", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _available(), reason=f"API 未启动({BASE})")


def test_health():
    r = httpx.get(f"{BASE}/api/health", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"]["database_name"] == "danqiu_rice"


def test_dashboard_summary():
    body = httpx.get(f"{BASE}/api/dashboard/summary", timeout=5).json()
    for key in ("farmers", "active_plots", "loan_applications", "orders", "sales_amount"):
        assert key in body
    assert body["farmers"] >= 1  # 种子数据约 200 户


def test_farmers_list():
    rows = httpx.get(f"{BASE}/api/farmers", timeout=5).json()
    assert isinstance(rows, list) and rows
    first = rows[0]
    assert {"id", "real_name", "village", "plot_count", "total_area_mu"} <= set(first)


def test_plot_detail():
    rows = httpx.get(f"{BASE}/api/farmers", timeout=5).json()
    plots = httpx.get(f"{BASE}/api/dashboard/summary", timeout=5).json()
    assert plots["active_plots"] >= 1
    # 逐个尝试前几个农户名下不一定有地块,直接用 plot id 1..5 探测
    found = None
    for pid in range(1, 6):
        r = httpx.get(f"{BASE}/api/plots/{pid}", timeout=5)
        if r.status_code == 200:
            found = r.json()
            break
    assert found, "前 5 个地块 ID 均不存在,种子数据异常"
    assert "records" in found and "certifications" in found
    assert rows


def test_trace_not_found():
    r = httpx.get(f"{BASE}/api/trace/NOT_EXIST_CODE", timeout=5)
    assert r.status_code == 404


def test_loans_claims_orders():
    assert isinstance(httpx.get(f"{BASE}/api/loans", timeout=5).json(), list)
    assert isinstance(httpx.get(f"{BASE}/api/claims", timeout=5).json(), list)
    assert isinstance(httpx.get(f"{BASE}/api/orders", timeout=5).json(), list)


def test_government_summary():
    body = httpx.get(f"{BASE}/api/government/summary", timeout=5).json()
    assert {"certified_farmers", "inspection_warnings", "missing_or_wrong_records", "pending_reports"} <= set(body)
