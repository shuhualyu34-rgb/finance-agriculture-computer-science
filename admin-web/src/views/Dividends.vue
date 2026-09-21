<template>
  <div class="page">
    <el-card>
      <template #header>
        品牌分红计算（基于扫码订单，可重复执行，幂等）
      </template>
      <el-button type="primary" size="large" :loading="loading" @click="calculate">开始分红计算</el-button>
      <el-row v-if="result" :gutter="16" style="margin-top: 24px">
        <el-col :span="6"><el-card shadow="hover"><div class="stat-card"><div class="num">{{ result.orders_scanned }}</div><div>参与扫码订单</div></div></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><div class="stat-card"><div class="num">{{ result.dividends_created }}</div><div>生成分红记录</div></div></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><div class="stat-card"><div class="num">{{ (result.dividend_rate * 100).toFixed(1) }}%</div><div>分红比例</div></div></el-card></el-col>
        <el-col :span="6"><el-card shadow="hover"><div class="stat-card"><div class="num">{{ fmtMoney(result.total_dividend_amount) }}</div><div>分红总额</div></div></el-card></el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtMoney } from '../utils/format'

const loading = ref(false)
const result = ref(null)

async function calculate() {
  loading.value = true
  try {
    result.value = await http.post('/api/admin/dividends/calculate')
    ElMessage.success('分红计算完成')
  } finally { loading.value = false }
}
</script>

<style scoped>
.num { font-size: 26px; font-weight: bold; color: #409eff; margin-bottom: 6px; }
</style>
