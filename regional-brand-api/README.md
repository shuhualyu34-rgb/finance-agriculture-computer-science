# 区域公用品牌标准化运营与助农增收平台 API

本目录包含平台 RESTful API 的初版设计稿，可用于 Swagger UI、Apifox、Postman 或后端接口开发。

## 文件说明

- `openapi.yaml`：OpenAPI 3.0 接口定义，可导入 Swagger UI、Apifox、Postman。
- `API-DESIGN.md`：面向产品、前端和后端团队的接口说明。

## 导入方式

将 `openapi.yaml` 导入 Apifox、Postman 或 Swagger Editor，即可生成接口目录和调试页面。

## 基础约定

- API 前缀：`/api/v1`
- 数据格式：`application/json`
- 鉴权：OAuth 2.0 Bearer Token
- 分页：`page` 从 1 开始，`pageSize` 最大 100
- 时间：ISO 8601 格式
- 请求追踪：推荐携带 `X-Request-Id`

