# API 接口设计

## 统一响应

```json
{
  "code": "SUCCESS",
  "message": "操作成功",
  "requestId": "req_202609180001",
  "data": {},
  "timestamp": "2026-09-18T10:30:00+08:00"
}
```

## 接口清单

| 模块 | 方法 | 路径 | 说明 |
|---|---|---|---|
| M1 | POST | `/standards` | 创建标准库版本 |
| M1 | GET | `/standards` | 查询标准库 |
| M1 | POST | `/batches` | 创建产品批次 |
| M1 | GET | `/batches` | 查询产品批次 |
| M1 | GET | `/batches/{batchId}` | 查询批次详情 |
| M1 | POST | `/batches/{batchId}/quality-inspections` | 提交批次品控检查 |
| M1 | GET | `/packaging-logistics-standards` | 查询包装与流通规范 |
| M2 | POST | `/subjects/{subjectId}/qualification-reviews` | 提交主体资质审核 |
| M2 | POST | `/subjects` | 创建主体入驻申请 |
| M2 | GET | `/subjects/{subjectId}` | 查询主体详情 |
| M2 | POST | `/brand-authorizations` | 申请品牌授权 |
| M2 | PUT | `/brand-authorizations/{authorizationId}/review` | 审批品牌授权 |
| M2 | POST | `/brands/{brandId}/visual-assets` | 上传 VI 品牌素材 |
| M3 | POST | `/quality-service-orders` | 创建品控服务工单 |
| M3 | POST | `/channel-matches` | 发布渠道撮合需求 |
| M3 | POST | `/training-records` | 提交培训报名记录 |
| M3 | POST | `/settlements` | 生成利益分配结算单 |
| M4 | POST | `/marketing-campaigns` | 创建电商营销活动 |
| M4 | POST | `/agri-tourism-projects` | 创建农旅项目 |
| M4 | POST | `/cultural-contents` | 创建文化赋能内容 |
| M4 | GET | `/traceability/{traceCode}` | 查询消费者溯源信息 |
| M4 | POST | `/batches/{batchId}/trace-code` | 生成批次溯源码 |

## 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
X-Tenant-Id: tenant_100001
X-Request-Id: req_202609180001
```

## OAuth 2.0 与认证

采用 Authorization Code + PKCE。品牌授权、批次创建、订单和结算等操作要求实名；企业主体相关操作还要求企业认证。

常用作用域：`openid`、`profile`、`standard:read`、`standard:write`、`quality:write`、`brand:apply`、`brand:review`、`channel:match:create`、`settlement:create`、`marketing:campaign:create`、`content:write`。

## 错误码

| HTTP | 错误码 | 说明 |
|---:|---|---|
| 400 | `PARAM_INVALID` | 参数校验失败 |
| 401 | `AUTH_TOKEN_INVALID` | Token 无效或过期 |
| 403 | `PERMISSION_DENIED` | 无操作权限 |
| 403 | `REALNAME_REQUIRED` | 需要实名认证 |
| 403 | `ENTERPRISE_VERIFY_REQUIRED` | 需要企业认证 |
| 404 | `RESOURCE_NOT_FOUND` | 资源不存在 |
| 409 | `STATE_CONFLICT` | 当前状态不允许操作 |
| 422 | `BUSINESS_RULE_VIOLATION` | 不符合业务规则 |
| 429 | `RATE_LIMITED` | 请求频率超限 |
| 500 | `INTERNAL_ERROR` | 系统内部错误 |
