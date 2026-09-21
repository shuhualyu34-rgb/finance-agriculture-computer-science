# 丹邱丝苗米普惠产融服务平台

> 中国国际大学生创新大赛 · 乡村特色农业全产业链数字化赋能与普惠金融
> 广州增城朱村街丹邱村丝苗米产业数字化平台

需求文档:`丹邱丝苗米普惠产融服务平台-产品需求文档v5.docx`

## 七端总览

| 端 | 形态 | 核心功能 |
|---|---|---|
| 农户端 | 手机 H5 | 上传农事、申请认证/保险/贷款、查看分红 |
| 消费端 | 手机 H5(扫码) | 溯源、卫星图、农事时间线、认养、商城 |
| 银行端 | Web | 授信建议、农户画像、自行审批 |
| 保险公司端 | Web | 保单管理、理赔复核 |
| 品牌运营端 | Web | 标准、认证审批、授权、溯源码、订单/分红 |
| 政府监管端 | Web 大屏 | 产业总览、合规预警、监管报表(周/月/季) |
| 系统管理后台 | Web | 用户、农户、认养、参数配置 |

## 快速启动(Docker)

```bash
# 首次启动:自动建库、导入 schema 与 200 户种子数据
docker-compose up -d --build

# API 地址
#   接口文档: http://127.0.0.1:8010/docs
#   健康检查: http://127.0.0.1:8010/api/health
# MySQL(宿主机调试): 127.0.0.1:3307  root / danqiu_dev_root(可用 .env 覆盖)
```

常用命令:

```bash
docker-compose ps            # 状态
docker-compose logs -f api   # 看后端日志
docker-compose down          # 停止(保留数据)
docker-compose down -v       # 停止并清空数据库
```

> 重新导入数据:`docker-compose down -v && docker-compose up -d`

## 本地开发(不依赖 Docker 后端部分)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r backend/requirements.txt -r requirements-dev.txt
set DANQIU_DB_HOST=127.0.0.1
set DANQIU_DB_PORT=3307
set DANQIU_DB_PASSWORD=danqiu_dev_root
uvicorn backend.app:app --reload --port 8010
```

(macOS/Linux 见 `start_danqiu_backend.sh`)

## 测试与检查

```bash
.venv\Scripts\activate
ruff check .                  # 静态检查
pytest                        # 单元 + 集成(API 未启动时集成用例自动跳过)
```

## 目录结构

```
backend/                 FastAPI 后端(当前:Phase 1 只读 API)
  app.py                 8 个只读接口 + health
  tests/                 pytest 测试
regional-brand-api/      区域公用品牌平台 API 设计稿(OpenAPI 3.0,B 线)
danqiu_platform_schema.sql   数据库结构(24 张表,含建库语句)
danqiu_rice_seed.sql         种子数据(200 户,由 generate_danqiu_seed.py 生成)
danqiu_platform_mock.sql     小规模演示数据(与种子数据二选一)
docker-compose.yml       db(mysql:8.0) + api(FastAPI)
Dockerfile               后端镜像
*.html                   各端静态原型
```

## 核心业务规则(PRD 第六节)

- **保险**:保额 = 面积 × 1500 元/亩;总保费 = 保额 × 5%(政府补贴 80%、农户自缴 20%);赔付 = 保额 × 受灾比例
- **贷款建议**:建议额度 = 面积 × 800 元/亩;风险评级:认证+保险=低、无保险=中、信息不全=高(系统只出建议,银行自行决定)
- **本期不做**(MVP 边界):真实短信/支付、物联网、卫星实时计算、真实放款、区块链/大模型

## 开发路线

- [x] 阶段 0:工程基线(Docker 化、git、测试基线)
- [ ] 阶段 1:鉴权 + 农户端/消费端 H5 + 写入闭环(农事上传 → 认证/保险/贷款申请 → 订单/认养/分红)
- [ ] 阶段 2:银行/保险/品牌运营/政府监管 Web 端 + 监管报表
- [ ] 阶段 3:B 线区域公用品牌平台(见 regional-brand-api/)
