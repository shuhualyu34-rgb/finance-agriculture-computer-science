<template>
  <div class="page">
    <el-card style="max-width: 620px">
      <template #header>保险产品参数配置（修改后新投保按新参数计算）</template>
      <div v-for="p in products" :key="p.id" class="product-block">
        <h4>{{ p.product_name }}</h4>
        <el-form label-width="120px" style="max-width: 460px">
          <el-form-item label="保额（元/亩）">
            <el-input-number v-model="p.insured_amount_per_mu" :min="0" :step="100" />
          </el-form-item>
          <el-form-item label="保费率（%）">
            <el-input-number v-model="p.premium_rate_percent" :min="0" :max="100" :step="0.1" />
          </el-form-item>
          <el-form-item label="政府补贴率（%）">
            <el-input-number v-model="p.government_subsidy_rate_percent" :min="0" :max="100" :step="1" />
          </el-form-item>
          <el-form-item label="状态">
            <el-tag :type="p.status === 'ACTIVE' ? 'success' : 'info'">{{ p.status === 'ACTIVE' ? '在售' : '停用' }}</el-tag>
          </el-form-item>
          <el-button type="primary" :loading="savingId === p.id" @click="save(p)">保存</el-button>
        </el-form>
        <el-divider />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const products = ref([])
const savingId = ref(null)

function toPercent(v) { return Math.round((v || 0) * 10000) / 100 }
function fromPercent(v) { return Math.round(v * 100) / 10000 }

async function load() {
  const list = await http.get('/api/admin/insurance-products')
  products.value = list.map((p) => ({
    ...p,
    premium_rate_percent: toPercent(p.premium_rate),
    government_subsidy_rate_percent: toPercent(p.government_subsidy_rate)
  }))
}

async function save(p) {
  savingId.value = p.id
  try {
    await http.put('/api/admin/insurance-products/' + p.id, {
      insured_amount_per_mu: p.insured_amount_per_mu,
      premium_rate: fromPercent(p.premium_rate_percent),
      government_subsidy_rate: fromPercent(p.government_subsidy_rate_percent)
    })
    ElMessage.success('保存成功')
  } finally { savingId.value = null }
}

onMounted(load)
</script>
