# 丹邱丝苗米普惠产融服务平台 · H5 前端（农户端 + 消费端）

Vite + Vue3（JS）+ Vant 4 + vue-router，无 Pinia，token 存 localStorage。全部调用后端真实接口（无 mock 数据）。

## 启动方式

```bash
cd frontend
npm install            # 失败/超时可加 --registry=https://registry.npmmirror.com
npm run dev            # http://localhost:5173
npm run build          # 产物在 dist/
```

- 后端需运行在 `http://127.0.0.1:8010`（dev server 已配置 `/api`、`/uploads` 代理转发）。
- 端口固定 5173（见 `vite.config.js`）。

## 演示账号（验证码均为 1234）

| 角色 | 手机号 | 说明 |
| ---- | ------ | ---- |
| 农户 | 13800015892 | 黄强，多块田 |
| 消费者 | 13900015066 | 张玲 |

溯源演示码（免登录）：`0C2895566118471E`

## 页面清单

### 通用
- `/` 入口选择页（消费端 / 农户端）

### 农户端 `/farmer`
| 路由 | 页面 | 说明 |
| ---- | ---- | ---- |
| `/farmer/login` | 登录 | 手机号+验证码（提示演示验证码 1234） |
| `/farmer` | 首页 | 欢迎语、认证状态徽章、地块数/总面积、保单数、最新贷款建议、分红汇总、申请中心入口；底部 Tab |
| `/farmer/plots` | 我的田块 | 列表（名称/面积/品种/认证状态），点击进详情 |
| `/farmer/plots/:id` | 田块详情 | 基本信息 + 农事记录时间线 + 卫星图 |
| `/farmer/upload` | 农事上传 | 选地块、六种记录类型、日期（默认今天，不可选未来）、描述、投入品、产出、多图上传预览 |
| `/farmer/apply` | 申请中心 | 品牌认证（409 提示重复）/ 保险试算+投保 / 贷款建议额度+风险+依据 |
| `/farmer/mine` | 我的 | 贷款、保单、理赔、分红四个 Tab 列表 |

### 消费端 `/consumer`
| 路由 | 页面 | 说明 |
| ---- | ---- | ---- |
| `/consumer` | 溯源首页 | 输入溯源码查询（预填演示码+一键演示）；结果：地块/批次/等级/农户/卫星图/农事时间线（正序） |
| `/consumer/adopt` | 认养列表 | 需登录；卡片展示田块信息，确认弹窗模拟支付，成功提示单号 |
| `/consumer/mine` | 我的认养 | 需登录；认养单号、地块、费用、状态 |
| `/consumer/login` | 消费者登录 | 验证码 1234 |

## 实现说明

- `src/api.js`：fetch 封装，自动带 `Authorization: Bearer`，401 自动清 token 跳对应登录页。
- `src/constants.js`：所有枚举的中文映射（记录类型、银行结果、风险等级、认证/保单/理赔/分红状态、米质等级等）。
- 主色稻绿 `#4a7c59`，移动端 max-width 480px 居中。
- 图片走 `POST /api/uploads`，返回的 `/uploads/..` URL 经 dev proxy 直接可访问。
- 后端未提供「我的认养订单」查询接口（`/api/orders` 为销售订单表，与认养无关），`/consumer/mine` 展示本机真实下单成功的认养记录（localStorage）。
- 种子数据中卫星图为示例域名（danqiu.example.com），页面已做占位降级展示。
