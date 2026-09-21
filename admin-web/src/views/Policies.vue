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
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="toClaim(row)">录入理赔</el-button>
        </template>
      </el-table-column>
    </el-table>
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

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/insurance/policies', { params: status.value ? { status: status.value } : {} })
  } finally { loading.value = false }
}

function toClaim(row) {
  router.push({ path: '/claims/new', query: { policy_id: row.id } })
}

onMounted(load)
</script>
