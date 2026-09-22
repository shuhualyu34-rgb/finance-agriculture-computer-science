<template>
  <div>
    <van-nav-bar title="我的收入" left-arrow @click-left="$router.back()" />
    <div class="page page-no-tab">
      <div class="hero">
        <div class="sub" style="opacity:1">{{ year }} 年总收入（元）</div>
        <div style="font-size:30px;font-weight:700;margin-top:4px">{{ fmt2(summary.TOTAL) }}</div>
        <div class="sub">地租 + 务工工资 + 品牌溢价 + 平台销售分红</div>
      </div>

      <div style="margin-bottom:12px;display:flex;gap:8px">
        <van-button v-for="y in years" :key="y" size="small" :type="y === year ? 'primary' : 'default'"
          :color="y === year ? '#4a7c59' : ''" round @click="switchYear(y)">{{ y }} 年</van-button>
      </div>

      <div class="stat-grid">
        <div class="stat-item">
          <div class="num small">{{ fmt2(summary.RENT) }}</div>
          <div class="label">🏠 地租</div>
        </div>
        <div class="stat-item">
          <div class="num small">{{ fmt2(summary.WAGE) }}</div>
          <div class="label">👷 工资</div>
        </div>
        <div class="stat-item">
          <div class="num small">{{ fmt2(summary.BRAND_PREMIUM) }}</div>
          <div class="label">🏅 品牌溢价</div>
        </div>
      </div>
      <div class="stat-grid" style="grid-template-columns:1fr;margin-top:8px">
        <div class="stat-item">
          <div class="num small">{{ fmt2(summary.DIVIDEND) }}</div>
          <div class="label">🌾 平台销售分红</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">收入明细（{{ items.length }} 条）</div>
        <van-pull-refresh v-model="refreshing" @refresh="load">
          <div v-if="!loading && items.length === 0" class="muted" style="text-align:center;padding:24px 0">
            {{ year }} 年暂无收入记录
          </div>
          <div v-for="(it, i) in items" :key="i" style="padding:10px 0;border-bottom:1px solid #f0f0f0">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <van-tag :type="tagType(it.income_type)" plain>{{ mapOf(INCOME_TYPE, it.income_type) }}</van-tag>
              <span style="font-weight:700;color:#4a7c59">+¥{{ fmt2(it.amount) }}</span>
            </div>
            <div class="muted" style="margin-top:6px" v-if="it.remark">{{ it.remark }}</div>
            <div class="muted" style="margin-top:2px">{{ it.period }} 期 · {{ fmtDate(it.created_at) }}</div>
          </div>
        </van-pull-refresh>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import api from '../../api'
import { fmtDate } from '../../constants'

const INCOME_TYPE = {
  RENT: { text: '地租', color: '#4a7c59' },
  WAGE: { text: '工资', color: '#1976d2' },
  BRAND_PREMIUM: { text: '品牌溢价', color: '#c9a24b' },
  DIVIDEND: { text: '平台分红', color: '#9c27b0' },
}
function mapOf(dict, key) {
  const v = dict[key]
  return v ? v.text : key || '-'
}
function tagType(key) {
  switch (key) {
    case 'RENT': return 'success'
    case 'WAGE': return 'primary'
    case 'BRAND_PREMIUM': return 'warning'
    case 'DIVIDEND': return 'default'
    default: return 'default'
  }
}
function fmt2(v) {
  return Number(v || 0).toFixed(2)
}

const currentYear = new Date().getFullYear()
const years = [currentYear, currentYear - 1]
const year = ref(String(currentYear))
const summary = ref({ RENT: 0, WAGE: 0, BRAND_PREMIUM: 0, DIVIDEND: 0, TOTAL: 0 })
const items = ref([])
const loading = ref(true)
const refreshing = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await api.get('/api/my/income?year=' + year.value)
    summary.value = data.summary || {}
    items.value = data.items || []
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}
function switchYear(y) {
  if (year.value === y) return
  year.value = y
  load()
}
onMounted(load)
</script>
