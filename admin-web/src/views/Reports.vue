<template>
  <div class="page">
    <div class="toolbar no-print">
      <el-button type="primary" :loading="generating === 'WEEKLY'" @click="generate('WEEKLY')">生成周报</el-button>
      <el-button type="primary" :loading="generating === 'MONTHLY'" @click="generate('MONTHLY')">生成月报</el-button>
      <el-button type="primary" :loading="generating === 'QUARTERLY'" @click="generate('QUARTERLY')">生成季报</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe class="no-print">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">{{ reportTypeMap[row.report_type] || row.report_type }}</template>
      </el-table-column>
      <el-table-column prop="report_period" label="周期" min-width="120" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="row.status === 'CONFIRMED' ? 'success' : row.status === 'ARCHIVED' ? 'info' : 'warning'">
            {{ reportStatusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="确认时间" width="150">
        <template #default="{ row }">{{ fmtDateTime(row.confirmed_at) }}</template>
      </el-table-column>
      <el-table-column label="生成时间" width="150">
        <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="detailVisible" size="720px" :title="detailTitle" :close-on-click-modal="false">
      <div v-if="detail" class="print-area">
        <h2 style="text-align: center">{{ detailTitle }}</h2>
        <p style="text-align: center; color: #606266">
          统计区间：{{ detail.content?.period_range?.[0] }} ~ {{ detail.content?.period_range?.[1] }}
          ｜ 状态：{{ reportStatusMap[detail.status] }}
        </p>

        <h4>一、农户情况</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="农户总数">{{ detail.content?.farmers?.total }}</el-descriptions-item>
          <el-descriptions-item label="已认证">{{ detail.content?.farmers?.certified }}</el-descriptions-item>
        </el-descriptions>

        <h4>二、生产合规</h4>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="农事记录数">{{ detail.content?.production?.records }}</el-descriptions-item>
          <el-descriptions-item label="需修正记录">{{ detail.content?.production?.needs_correction }}</el-descriptions-item>
          <el-descriptions-item label="合规率">
            <span :style="{ color: complianceColor }">{{ complianceRate }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <template v-if="missingFarmers.length">
          <p style="color: #f56c6c; font-weight: bold">缺漏农事记录名单（标红）：</p>
          <el-table :data="missingFarmers" size="small" border>
            <el-table-column prop="real_name" label="农户" width="120" />
            <el-table-column prop="phone" label="电话" width="140" />
            <el-table-column prop="plot_name" label="地块" />
          </el-table>
        </template>

        <h4>三、巡检情况</h4>
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="巡检总数">{{ detail.content?.inspections?.total }}</el-descriptions-item>
          <el-descriptions-item label="合格">{{ detail.content?.inspections?.passed }}</el-descriptions-item>
          <el-descriptions-item label="违规">{{ detail.content?.inspections?.violations }}</el-descriptions-item>
          <el-descriptions-item label="整改率">{{ pct(detail.content?.inspections?.rectification_rate) }}</el-descriptions-item>
        </el-descriptions>

        <h4>四、保险情况</h4>
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="保单数">{{ detail.content?.insurance?.policies }}</el-descriptions-item>
          <el-descriptions-item label="总保额">{{ fmtMoney(detail.content?.insurance?.insured_amount) }}</el-descriptions-item>
          <el-descriptions-item label="理赔数">{{ detail.content?.insurance?.claims }}</el-descriptions-item>
          <el-descriptions-item label="已赔付">{{ fmtMoney(detail.content?.insurance?.paid_amount) }}</el-descriptions-item>
        </el-descriptions>

        <h4>五、贷款情况</h4>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="申请数">{{ detail.content?.loans?.applications }}</el-descriptions-item>
          <el-descriptions-item label="批准数">{{ detail.content?.loans?.approved }}</el-descriptions-item>
          <el-descriptions-item label="放款金额">{{ fmtMoney(detail.content?.loans?.amount) }}</el-descriptions-item>
        </el-descriptions>

        <h4>六、销售情况</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单数">{{ detail.content?.sales?.orders }}</el-descriptions-item>
          <el-descriptions-item label="销售额">{{ fmtMoney(detail.content?.sales?.amount) }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="detail.content?.site_note">
          <h4>现场备注</h4>
          <p style="background: #fdf6ec; padding: 10px; border-radius: 4px">{{ detail.content.site_note }}</p>
        </template>

        <div class="no-print" style="margin-top: 20px; display: flex; gap: 12px">
          <el-button v-if="detail.status === 'DRAFT'" type="success" @click="confirmVisible = true">确认上报</el-button>
          <el-button type="primary" @click="doPrint">打印 / 导出PDF</el-button>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="confirmVisible" title="确认上报" width="440px">
      <el-form label-width="80px">
        <el-form-item label="现场备注">
          <el-input v-model="confirmNote" type="textarea" :rows="3" placeholder="请填写现场核查备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmVisible = false">取消</el-button>
        <el-button type="success" :loading="confirming" @click="submitConfirm">确认上报</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtDateTime, fmtMoney, reportTypeMap, reportStatusMap } from '../utils/format'

const rows = ref([])
const loading = ref(false)
const generating = ref('')
const detailVisible = ref(false)
const detail = ref(null)
const detailTitle = ref('')
const confirmVisible = ref(false)
const confirmNote = ref('')
const confirming = ref(false)

const missingFarmers = computed(() => detail.value?.content?.production?.missing_farmers || [])
const complianceRate = computed(() => pct(detail.value?.content?.production?.compliance_rate))
const complianceColor = computed(() => {
  let v = Number(detail.value?.content?.production?.compliance_rate || 0)
  if (v <= 1) v = v * 100 // 兼容 0~1 口径
  return v >= 90 ? '#67c23a' : v >= 70 ? '#e6a23c' : '#f56c6c'
})

function pct(v) {
  if (v === null || v === undefined || v === '') return '-'
  // 兼容两种口径：后端可能返回 0~1 小数或已是百分数的数值
  return (v > 1 ? v : v * 100).toFixed(1) + '%'
}

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/government/reports')
  } finally { loading.value = false }
}

async function generate(type) {
  generating.value = type
  try {
    const res = await http.post('/api/government/reports/generate', { report_type: type })
    ElMessage.success((res.created ? '已生成' : '已重建（同周期幂等）') + '：' + reportTypeMap[type] + ' ' + res.report_period)
    load()
  } finally { generating.value = '' }
}

async function openDetail(row) {
  detail.value = null
  detailTitle.value = '监管' + (reportTypeMap[row.report_type] || row.report_type) + '（' + row.report_period + '）'
  detailVisible.value = true
  detail.value = await http.get('/api/government/reports/' + row.id)
  detailTitle.value = '监管' + (reportTypeMap[detail.value.report_type] || '') + '（' + detail.value.report_period + '）'
}

async function submitConfirm() {
  confirming.value = true
  try {
    await http.put('/api/government/reports/' + detail.value.id + '/confirm', { note: confirmNote.value })
    ElMessage.success('已确认上报')
    confirmVisible.value = false
    detailVisible.value = false
    load()
  } finally { confirming.value = false }
}

function doPrint() {
  document.body.classList.add('printing-detail')
  window.print()
  window.addEventListener('afterprint', () => document.body.classList.remove('printing-detail'), { once: true })
}

onMounted(load)
</script>
