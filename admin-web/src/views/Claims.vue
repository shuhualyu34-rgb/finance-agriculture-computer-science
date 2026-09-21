<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="status" clearable placeholder="全部状态" style="width: 160px" @change="load">
        <el-option v-for="(t, k) in claimStatusMap" :key="k" :label="t" :value="k" />
      </el-select>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="claim_no" label="理赔单号" width="150" />
      <el-table-column prop="policy_no" label="保单号" width="150" />
      <el-table-column prop="farmer_name" label="农户" width="90" />
      <el-table-column prop="plot_name" label="地块" min-width="110" />
      <el-table-column prop="disaster_note" label="受灾说明" min-width="140" />
      <el-table-column label="受灾比例" width="90">
        <template #default="{ row }">{{ Math.round(row.disaster_rate * 100) }}%</template>
      </el-table-column>
      <el-table-column label="赔付金额" width="110">
        <template #default="{ row }">{{ fmtMoney(row.claim_amount) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'PAID' ? 'success' : row.status === 'REJECTED' ? 'danger' : row.status === 'APPROVED' ? 'primary' : 'warning'">
            {{ claimStatusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="复核时间" width="140">
        <template #default="{ row }">{{ fmtDateTime(row.reviewed_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'SUBMITTED' || row.status === 'APPROVED'" link type="primary" @click="openReview(row)">复核</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="理赔复核" width="440px">
      <p>理赔单号：{{ current?.claim_no }}，赔付金额 {{ fmtMoney(current?.claim_amount) }}</p>
      <el-radio-group v-model="reviewStatus">
        <el-radio label="APPROVED" :disabled="current?.status === 'APPROVED'">复核通过</el-radio>
        <el-radio label="REJECTED">驳回</el-radio>
        <el-radio label="PAID" :disabled="current?.status === 'SUBMITTED'">标记已赔付</el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtDateTime, fmtMoney, claimStatusMap } from '../utils/format'

const status = ref('')
const rows = ref([])
const loading = ref(false)
const visible = ref(false)
const current = ref(null)
const reviewStatus = ref('APPROVED')
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/insurance/claims', { params: status.value ? { status: status.value } : {} })
  } finally { loading.value = false }
}

function openReview(row) {
  current.value = row
  reviewStatus.value = row.status === 'SUBMITTED' ? 'APPROVED' : 'PAID'
  visible.value = true
}

async function submit() {
  saving.value = true
  try {
    await http.put('/api/insurance/claims/' + current.value.id + '/review', { status: reviewStatus.value })
    ElMessage.success('复核完成')
    visible.value = false
    load()
  } finally { saving.value = false }
}

onMounted(load)
</script>
