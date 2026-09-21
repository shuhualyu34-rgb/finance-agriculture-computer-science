export function fmtDateTime(s) {
  if (!s) return '-'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes())
}

export function fmtMoney(n) {
  if (n === null || n === undefined || n === '') return '-'
  return '¥' + Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export const loanResultMap = { PENDING: '待审批', APPROVED: '已通过', REJECTED: '已驳回' }
export const certStatusMap = { PENDING: '待审核', APPROVED: '已通过', REJECTED: '已驳回', RECTIFYING: '退回整改', CERTIFIED: '已认证', UNCERTIFIED: '未认证' }
export const policyStatusMap = { PENDING: '待生效', APPLIED: '已投保', ACTIVE: '保障中', EXPIRED: '已到期', CLAIMED: '已理赔' }
export const claimStatusMap = { SUBMITTED: '待复核', APPROVED: '复核通过', REJECTED: '已驳回', PAID: '已赔付' }
export const traceStatusMap = { ACTIVE: '启用', DISABLED: '已停用' }
export const userStatusMap = { ACTIVE: '正常', DISABLED: '已禁用' }
export const roleMap = {
  FARMER: '农户', CONSUMER: '消费者', BANK: '银行', INSURANCE: '保险',
  OPERATOR: '品牌运营', GOVERNMENT: '政府', ADMIN: '管理员'
}
export const stageMap = {
  PLANTING: '种植', PROCESSING: '加工', QUALITY: '品控',
  GRADING: '分级', PACKAGING: '包装', DISTRIBUTION: '流通'
}
export const gradeMap = { SPECIAL: '特级', FIRST: '一级', SECOND: '二级' }
export const riskMap = { LOW: '低风险', MEDIUM: '中风险', HIGH: '高风险' }
export const orderStatusMap = { PENDING_PAYMENT: '待支付', PAID: '待发货', SHIPPED: '已发货', COMPLETED: '已完成' }
