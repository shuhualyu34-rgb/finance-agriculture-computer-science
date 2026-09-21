# 丹邱丝苗米平台后端

连接数据库 `danqiu_rice` 的只读 API(Phase 1),用于把现有 HTML 原型接到真实数据。

## 启动

### 方式一:Docker(推荐)

项目根目录执行:

```bash
docker-compose up -d --build
```

- 健康检查:`http://127.0.0.1:8010/api/health`
- 接口文档:`http://127.0.0.1:8010/docs`

### 方式二:本地虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows;macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

set DANQIU_DB_HOST=127.0.0.1     # 指向 Docker 暴露的 MySQL
set DANQIU_DB_PORT=3307
set DANQIU_DB_USER=root
set DANQIU_DB_PASSWORD=danqiu_dev_root
uvicorn backend.app:app --reload --port 8010
```

(macOS/Linux 交互式启动见根目录 `start_danqiu_backend.sh`)

## 当前接口

- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/farmers`
- `GET /api/plots/{plot_id}`
- `GET /api/trace/{code}`
- `GET /api/loans`
- `GET /api/claims`
- `GET /api/orders`
- `GET /api/government/summary`

本阶段只读,不实现真实支付、贷款放款、保险自动定损或数据写入。

## 测试

```bash
pytest backend/tests            # 或根目录直接 pytest
```
