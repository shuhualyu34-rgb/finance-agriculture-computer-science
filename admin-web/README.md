# 丹邱丝苗米普惠产融服务平台 · 管理后台（admin-web）

Vite + Vue3(JS) + Element Plus + vue-router + axios 的管理后台，对接 FastAPI 后端（http://127.0.0.1:8010）。

## 启动方式

```bash
cd admin-web
npm install --registry=https://registry.npmmirror.com
# 若 esbuild postinstall 被拦截：cd node_modules/esbuild && node install.js && cd ../..
npm run dev     # http://localhost:5174  /api、/uploads 已代理到 127.0.0.1:8010
npm run build   # 产物在 dist/
```

要求后端已在 8010 端口运行。登录验证码固定 **1234**。

## 演示账号

| 角色 | 手机号 | 验证码 |
| --- | --- | --- |
| 银行 | 13764807553 | 1234 |
| 保险 | 13753091709 | 1234 |
| 品牌运营 | 13799943797 | 1234 |
| 管理员 | 13765250068 | 1234 |

## 页面清单（左侧菜单按角色动态显示）

| 路由 | 页面 | 可见角色 | 功能 |
| --- | --- | --- | --- |
| /login | 登录页 | 公开 | 手机号+验证码登录，四个演示账号一键填入 |
| /loans | 授信审批 | BANK / ADMIN | 状态 Tab 筛选；行操作「画像」（抽屉：基本信息/地块/保单/最近30条农事）与「审批」（通过/驳回+备注） |
| /policies | 保单管理 | INSURANCE / ADMIN | 保单列表 + 状态筛选；「录入理赔」带入保单跳转理赔处理 |
| /claims/new | 理赔处理 | INSURANCE / ADMIN | 选保单 + 受灾说明 + 受灾比例滑杆(0-100%)，实时预览赔付金额（保额×比例），提交 |
| /claims | 理赔台账 | INSURANCE / ADMIN | 理赔列表 + 状态筛选；复核（通过/驳回/已赔付） |
| /certifications | 认证审批 | OPERATOR / ADMIN | 待审列表 Tab；通过（自动升级 CERTIFIED）/驳回/退回整改 + 备注 |
| /standards | 标准管理 | OPERATOR / ADMIN | 版本下拉；六环节（种植/加工/品控/分级/包装/流通）分组条款展示 |
| /trace-codes | 溯源码管理 | OPERATOR / ADMIN | 列表 + 状态筛选；生成对话框（手输 plot_id 1~500 + 批次名 + 等级）；停用 |
| /orders | 订单管理 | OPERATOR / ADMIN | 状态 Tab（全部/待发货/已发货/已完成）；表格（单号/消费者/商品摘要/金额/状态/物流/时间/收货信息弹层解析 address_snapshot）；PAID 订单「发货」弹窗填快递公司+单号 |
| /dividends | 分红计算 | OPERATOR / ADMIN | 一键计算（幂等）+ 结果统计卡片（扫码订单/分红记录/比例/总额） |
| /users | 用户管理 | ADMIN | 表格 + 角色筛选 + 姓名/手机号搜索 |
| /plots | 认养管理 | ADMIN | 地块表格 + 认养开关（el-switch 调 PUT adoption） |
| /config | 数据配置 | ADMIN | 保险产品参数表单（保额/亩、保费率%、政府补贴率%）+ 保存 |
| /no-permission | 无权限提示 | — | 登录用户无任何后台角色时提示 |

金额、状态枚举均显示中文；时间格式 YYYY-MM-DD HH:mm；401 自动跳转登录页。

## 目录结构

```
admin-web/
├── index.html
├── vite.config.js        # 端口 5174，代理 /api /uploads → 127.0.0.1:8010
└── src/
    ├── main.js           # Element Plus（中文 locale）
    ├── api/index.js      # axios 封装（Bearer 头、401 拦截）
    ├── router/index.js   # 路由 + 角色守卫
    ├── store/auth.js     # 登录态（localStorage）
    ├── layout/AppLayout.vue  # 左侧菜单 + 顶部栏（标题/用户名/退出）
    ├── utils/format.js   # 金额/状态枚举/时间格式化
    └── views/            # Login / Loans / Policies / ClaimCreate / Claims /
                          # Certifications / Standards / TraceCodes / Dividends /
                          # Users / Plots / Config / NoPermission
```
