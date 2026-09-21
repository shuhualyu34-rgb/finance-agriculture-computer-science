# 丹邱丝苗米平台后端

这是第一阶段的只读 API，连接数据库 `danqiu_rice`，用于把现有 HTML 原型接到真实数据。

## 启动

在项目根目录执行：

```bash
source .venv/bin/activate
export DANQIU_DB_USER=root
export DANQIU_DB_PASSWORD='你的 MySQL 密码'
uvicorn backend.app:app --reload --port 8010
```

健康检查：`http://127.0.0.1:8010/api/health`

接口文档：`http://127.0.0.1:8010/docs`

## 当前接口

- `GET /api/dashboard/summary`
- `GET /api/farmers`
- `GET /api/plots/{plot_id}`
- `GET /api/trace/{code}`
- `GET /api/loans`
- `GET /api/claims`
- `GET /api/orders`
- `GET /api/government/summary`

本阶段只读，不实现真实支付、贷款放款、保险自动定损或数据写入。
