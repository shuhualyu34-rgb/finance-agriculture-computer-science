# PRD 验收标准对照表(§九)

> 更新时间:阶段 2(后端 + 政府大屏完成;银行/保险/运营/管理 Web 界面开发中)

| # | PRD 验收标准 | 状态 | 实现位置 | 验证方式 |
|---|---|---|---|---|
| 1 | 七个端全部可访问可操作 | 🟡 部分 | 农户端/消费端 H5 已完成(frontend/,http://localhost:5173);银行/保险/品牌运营/管理/政府端 API 已就绪,Web 界面待阶段 2 | frontend/ + /docs |
| 2 | 农户可上传农事记录,数据在消费端可见 | ✅ | POST /api/my/records + photos;消费端 GET /api/trace/{code} 含 production_records | pytest test_upload_and_create_record / test_farmer_summary |
| 3 | 消费者扫溯源码能看到地块信息、卫星图、农事记录 | ✅ 后端 | GET /api/trace/{code}(公开);卫星图 URL + 农事时间线 | 演示码 0C2895566118471E |
| 4 | 消费者可认养一块田 | ✅ | GET /api/adoption/plots + POST /api/adoption/orders(模拟支付即 PAID)+ GET /api/my/adoptions 我的认养 | pytest test_consumer_adoption |
| 5 | 农户可申请贷款,系统生成建议,银行自行审批 | ✅ | POST /api/my/loans(面积×800 建议 + 风险评级)+ PUT /api/bank/loans/{id}/review | pytest test_loan_apply_and_bank_review |
| 6 | 管理员可录入受灾情况触发理赔,保险公司复核 | ✅ | POST /api/insurance/claims(赔付=保额×受灾比例)+ PUT /claims/{id}/review | pytest test_claim_flow |
| 7 | 政府大屏数字随后台更新 | ✅ | bigscreen/ 随 API 发布(http://127.0.0.1:8010/bigscreen/):17 项指标卡片实时聚合、415 块地边界地图(认证着色/认养描边)、业务动态滚动,每分钟自动刷新 | GET /api/government/dashboard + 页面实测 |

## PRD 业务规则一致性(§六)

- 保额 = 面积 × 1500 元/亩 → backend/rules.py + 单测
- 总保费 = 保额 × 5%,政府补贴 80%、农户自缴 20% → 同上(费率可由 insurance_product 配置覆盖)
- 赔付 = 保额 × 受灾比例(管理员录入)→ rules.claim_amount + CHECK 约束(0≤rate≤1)
- 贷款建议 = 面积 × 800 元/亩;风险:认证+保险=低、无保险=中、信息不全=高 → rules.loan_suggestion / risk_level
- 系统只出建议,银行自行决定 → 审批接口仅 BANK/ADMIN 可操作,可驳回

## MVP 边界遵守(§八)

- [x] 验证码写死 1234(config.fixed_captcha,生产替换短信通道即可)
- [x] 模拟支付:认养下单即 PAID,无真实支付调用
- [x] 无物联网接入:农事数据全部由农户手机端上传
- [x] 卫星图仅静态展示(satellite_image_url)
- [x] 无区块链/大模型依赖
