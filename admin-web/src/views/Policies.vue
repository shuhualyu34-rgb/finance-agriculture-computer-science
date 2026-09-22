<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="status" clearable placeholder="全部状态" style="width: 160px" @change="load">
        <el-option v-for="(t, k) in policyStatusMap" :key="k" :label="t" :value="k" />
      </el-select>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="policy_no" label="保单号" width="150" />
      <el-table-column prop="farmer_name" label="农户" width="90" />
      <el-table-column prop="farmer_phone" label="手机号" width="120" />
      <el-table-column prop="plot_name" label="地块" min-width="110" />
      <el-table-column prop="product_name" label="产品" min-width="110" />
      <el-table-column prop="insured_area_mu" label="投保面积(亩)" width="110" />
      <el-table-column label="保额" width="110">
        <template #default="{ row }">{{ fmtMoney(row.insured_amount) }}</template>
      </el-table-column>
      <el-table-column label="农户保费" width="110">
        <template #default="{ row }">{{ fmtMoney(row.farmer_premium) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ACTIVE' ? 'success' : row.status === 'CLAIMED' ? 'warning' : 'info'">
            {{ policyStatusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="投保时间" width="140">
        <template #default="{ row }">{{ fmtDateTime(row.applied_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="showYield(row)">产量预测</el-button>
          <el-button link type="primary" @click="toClaim(row)">录入理赔</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="yieldVisible" :title="'产量预测 - ' + (current?.plot_name || '')" width="480px">
      <template v-if="yieldData">
        <el-alert
          v-if="yieldData.model_status && !yieldData.model_status.enabled"
          type="warning" :closable="false" show-icon
          :title="yieldData.note || '产量模型未启用'"
          style="margin-bottom: 12px"
        />
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="预测亩产">
            {{ yieldData.predicted_per_mu != null ? yieldData.predicted_per_mu + ' 斤/亩' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="预测总产">
            {{ yieldData.predicted_output_jin != null ? yieldData.predicted_output_jin + ' 斤' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="历史实际亩产">
            {{ yieldData.actual_per_mu != null ? yieldData.actual_per_mu + ' 斤/亩' : '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item label="预测偏差">
            {{ yieldData.deviation_pct != null ? yieldData.deviation_pct + '%' : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        <el-alert
          v-if="yieldData.deviation_pct != null && yieldData.deviation_pct < -10"
          type="error" :closable="false" show-icon
          title="预测显著低于历史实际，建议评估减产/受灾风险"
          style="margin-top: 12px"
        />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api'
import { fmtDateTime, fmtMoney, policyStatusMap } from '../utils/format'

const router = useRouter()
const status = ref('')
const rows = ref([])
const loading = ref(false)
const yieldVisible = ref(false)
const yieldData = ref(null)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/insurance/policies', { params: status.value ? { status: status.value } : {} })
  } finally { loading.value = false }
}

async function showYield(row) {
  current.value = row
  yieldData.value = null
  yieldVisible.value = true
  try {
    yieldData.value = await http.get('/api/insurance/yield-prediction/' + row.plot_id)
  } catch (e) { /* 预测接口异常时保留空态 */ }
}

function toClaim(row) {
  router.push({ path: '/claims/new', query: { policy_id: row.id } })
}

onMounted(load)
</script>
