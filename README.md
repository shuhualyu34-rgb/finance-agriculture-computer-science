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
#   政府大屏: http://127.0.0.1:8010/bigscreen/  (随 API 容器发布,公开访问,每分钟刷新)
# MySQL(宿主机调试): 127.0.0.1:3307  root / danqiu_dev_root(可用 .env 覆盖)
```

前端两个应用(H5 与管理后台):

```bash
cd frontend  && npm run dev   # http://localhost:5173  农户端/消费端 H5
cd admin-web && npm run dev   # http://localhost:5174  银行/保险/运营/管理后台
```

> 大屏说明:PRD 指定高德地图 JS API,但其需要申请 Key;当前版本用 ECharts 直接渲染地块 GeoJSON 边界(415 块地按认证状态着色、开放认养紫描边),零外部依赖离线可用,后续有 Key 可叠加高德瓦片。

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
backend/                 FastAPI 后端(阶段 1:鉴权 + 写入闭环)
  app.py                 路由装配
  auth.py / config.py / db.py / rules.py / schemas.py
  routers/               overview(只读)/ auth / farmer / consumer / bank / insurance / admin / uploads / ml
  ml/                    算法模型(评分卡 + 产量预测,详见"算法模型"章节)
  tests/                 pytest(单元 + 全链路集成)
frontend/                H5 前端(农户端 + 消费端,Vite + Vue3 + Vant)
regional-brand-api/      区域公用品牌平台 API 设计稿(OpenAPI 3.0,B 线)
migrations/              增量迁移(001:认养开放标记)
danqiu_platform_schema.sql   数据库结构(24 张表,含建库语句)
danqiu_rice_seed.sql         种子数据(200 户,由 generate_danqiu_seed.py 生成)
docker-compose.yml       db(mysql:8.0) + api(FastAPI)
Dockerfile               后端镜像
*.html                   各端静态原型
```

## 阶段 1 API 概览

鉴权:`POST /api/auth/login`(手机号 + 验证码 1234)→ JWT Bearer。演示账号:

| 角色 | 手机号 | 说明 |
|---|---|---|
| 农户 | 13800015892 | 黄强,有多块地 |
| 消费者 | 13900015066 | 张玲 |
| 银行 | 13764807553 | 农行审批员 |
| 保险 | 13753091709 | 人保核保员 |
| 品牌运营 | 13799943797 | 品牌运营专员 |
| 政府监管 | 13731585546 | 农业局监管员 |
| 管理员 | 13765250068 | 平台管理员 |

- 农户端 `/api/my/*`:summary、plots、records(GET/POST)、certifications(GET/POST)、policies、insurance(POST)、loans(GET/POST)、claims、dividends、income(四类收入年汇总)
- 消费端:`GET /api/adoption/plots`、`POST /api/adoption/orders`(模拟支付)、商城 `/api/shop/*`(products/orders/pay/confirm/my-orders)
- 银行端 `/api/bank/*`:loans、farmers/{id} 画像、loans/{id}/review
- 保险端 `/api/insurance/*`:policies、claims(GET/POST/PUT review)
- 品牌运营 `/api/operator/*`:standards(六环节条款)、trace-codes(生成/停用);`/api/admin/*`:certifications 审批、dividends/calculate;商城 `/api/shop/orders` 发货
- 管理后台 `/api/admin/*`:users、plots(认养开关)、insurance-products(参数)
- 政府监管 `/api/government/*`:dashboard(大屏,公开)、reports(周/月/季生成/确认/留档)、inspections(实地采集,面积差异>20% 自动预警)
- 上传:`POST /api/uploads`(multipart)→ `/uploads/...` 静态访问
- 溯源演示码:`0C2895566118471E`

## 核心业务规则(PRD 第六节)

- **保险**:保额 = 面积 × 1500 元/亩;总保费 = 保额 × 5%(政府补贴 80%、农户自缴 20%);赔付 = 保额 × 受灾比例
- **贷款建议**:建议额度 = 面积 × 800 元/亩;风险评级:认证+保险=低、无保险=中、信息不全=高(系统只出建议,银行自行决定)
- **本期不做**(MVP 边界):真实短信/支付、物联网、卫星实时计算、真实放款、区块链/大模型

## 算法模型(阶段 2.5:银行端评分卡 + 保险端产量预测)

基于仓库内种子数据离线训练的轻量 ML 能力,不依赖 Docker/数据库即可复现。

### 模型与接口

| 模型 | 端 | 接口 | 输出 | 当前指标(种子数据) |
|---|---|---|---|---|
| 逻辑回归信用评分卡 | 银行端 | `GET /api/bank/credit-score/{farmer_id}`(需 BANK/ADMIN) | 评分(300-900)、违约概率、风险档 | AUC≈0.55(见下方边界说明) |
| 产量预测(随机森林,择优) | 保险端 | `GET /api/insurance/yield-prediction/{plot_id}`(需 INSURANCE/ADMIN) | 预测亩产、预测总产、与历史实际偏差 | R²≈0.50, MAE≈95 斤/亩 |

### 训练(离线,零外部依赖)

```bash
.venv\Scripts\activate                    # Windows;macOS/Linux 用 source .venv/bin/activate
python -m backend.ml.train_credit_scorecard   # → backend/ml/models/credit_scorecard.joblib
python -m backend.ml.train_yield_model        # → backend/ml/models/yield_model.joblib
```

数据源为仓库内 `danqiu_rice_seed.sql`(200 户/415 地块),由 `backend/ml/seed_loader.py` 直接解析,
无需启动 MySQL。模型文件已随仓库提交,clone 后接口即可使用。

### 质量门禁与边界(重要)

- 推理层内置质量门禁:评分卡 **AUC < 0.60**、产量模型 **R² < 0.20** 时自动降级为规则计算,
  响应中 `model_status.enabled=false` 并给出原因,避免输出误导性结果。
- **当前评分卡为降级状态**:种子数据的 `bank_result` 审批标签由生成器**随机生成**(与农户特征无关),
  因此 AUC≈0.55 无学习信号。接口会如实返回规则评分(与 PRD 风险规则同口径)。
- **启用真实评分卡**:接入真实信贷数据(或改进 `generate_danqiu_seed.py` 使审批结果与农户风险相关)后,
  重新运行训练脚本;AUC 达标后服务自动启用模型打分,无需改代码。
- 产量预测在种子数据上即有有效信号(R²≈0.50),接口直接可用,可作为理赔损失评估参考
  (预测亩产 vs 历史实际亩产的偏差)。

### 模块结构

```
backend/ml/
  seed_loader.py            种子 SQL 解析(训练数据源)
  features.py               特征工程(训练与推理共用)
  dataset.py                数据集构建(特征+标签)
  scorecard.py              评分卡分数换算
  train_credit_scorecard.py 评分卡训练脚本
  train_yield_model.py      产量模型训练脚本(线性回归 vs 随机森林择优)
  inference.py              模型加载/推理/质量门禁/规则降级
  models/                   joblib 模型产物(随仓库提交)
```

## 开发路线

- [x] 阶段 0:工程基线(Docker 化、git、测试基线)
- [x] 阶段 1a:后端鉴权 + 写入闭环
- [x] 阶段 1b:农户端/消费端 H5(frontend/,`npm run dev` → http://localhost:5173)
- [x] 阶段 2:银行/保险/品牌运营/政府监管 Web 端 + 在线商城闭环 + 政府大屏
- [x] 阶段 3:监管报表(周/月/季)+ 实地采集交叉核验 + 农户收入四类明细
- [x] 阶段 2.5(协作):银行信用评分卡 + 保险产量预测模型
- [ ] 阶段 3:B 线区域公用品牌平台(见 regional-brand-api/)
