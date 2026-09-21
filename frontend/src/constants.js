// 中文映射与公共常量
export const RECORD_TYPES = {
  SOWING: '播种',
  FERTILIZING: '施肥',
  PESTICIDE: '打药',
  IRRIGATION: '灌溉',
  HARVEST: '收割',
  QUALITY_TEST: '米质检测',
}

export const BANK_RESULT = {
  PENDING: '待审批',
  APPROVED: '已放款',
  REJECTED: '未通过',
}

export const RISK_LEVEL = {
  LOW: { text: '低风险', type: 'primary' },
  MEDIUM: { text: '中风险', type: 'warning' },
  HIGH: { text: '高风险', type: 'danger' },
}

export const CERT_STATUS = {
  PENDING: { text: '审核中', type: 'warning' },
  APPROVED: { text: '已认证', type: 'success' },
  REJECTED: { text: '未通过', type: 'danger' },
  NONE: { text: '未认证', type: 'default' },
}

export const POLICY_STATUS = {
  PENDING: '待生效',
  ACTIVE: '保障中',
  EXPIRED: '已到期',
  CLAIMED: '已理赔',
  CANCELLED: '已退保',
}

export const CLAIM_STATUS = {
  PENDING: '待审核',
  APPROVED: '已理赔',
  REJECTED: '已驳回',
}

export const DIVIDEND_STATUS = {
  PENDING: '待发放',
  PAID: '已发放',
}

export const ADOPTION_ORDER_STATUS = {
  PAID: '已支付',
  PENDING: '待支付',
  CANCELLED: '已取消',
}

export const PRODUCT_GRADE = {
  PREMIUM: '特级',
  FIRST: '一级',
  SECOND: '二级',
  THIRD: '三级',
}

export function mapOf(dict, key) {
  const v = dict[key]
  if (v == null) return key || '-'
  return typeof v === 'string' ? v : v.text
}

export function tagTypeOf(dict, key) {
  const v = dict[key]
  return v && v.type ? v.type : 'default'
}

export const DEMO_TRACE_CODE = '0C2895566118471E'
export const DEMO_CAPTCHA = '1234'

export function fmtMoney(v) {
  if (v == null) return '-'
  return '¥' + Number(v).toLocaleString('zh-CN')
}

export function fmtDate(s) {
  if (!s) return '-'
  return String(s).replace('T', ' ').slice(0, 16)
}
