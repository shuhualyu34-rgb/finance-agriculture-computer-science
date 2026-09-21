<template>
  <div class="page">
    <div class="hero">
      <div class="hello">您好，{{ userName }} 👋</div>
      <div class="sub">丹邱丝苗米 · 让每一粒米都有出处</div>
      <div style="margin-top:10px">
        <van-tag v-if="certText" :type="certType" size="large">品牌认证：{{ certText }}</van-tag>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-item">
        <div class="num">{{ summary.plots.plot_count }}</div>
        <div class="label">地块数</div>
      </div>
      <div class="stat-item">
        <div class="num">{{ summary.plots.total_area_mu }}</div>
        <div class="label">总面积(亩)</div>
      </div>
      <div class="stat-item">
        <div class="num">{{ summary.policies.policy_count }}</div>
        <div class="label">保单数</div>
      </div>
    </div>

    <div class="card" style="margin-top:12px">
      <div class="card-title">
        最新贷款建议
        <van-tag v-if="loan && loan.risk_level" :type="riskType" plain>{{ riskText }}</van-tag>
      </div>
      <template v-if="loan">
        <div class="row-line"><span class="k">申请编号</span><span>{{ loan.application_no }}</span></div>
        <div class="row-line"><span class="k">抵押面积</span><span>{{ loan.area_mu }} 亩</span></div>
        <div class="row-line"><span class="k">建议额度</span><span style="color:#4a7c59;font-weight:700">{{ fmtMoney(loan.suggested_amount) }}</span></div>
        <div class="row-line"><span class="k">银行结果</span><span>{{ bankText }}</span></div>
      </template>
      <div v-else class="muted">暂无贷款申请</div>
    </div>

    <div class="stat-grid">
      <div class="stat-item">
        <div class="num small">{{ fmtMoney(summary.dividends.total) }}</div>
        <div class="label">累计分红</div>
      </div>
      <div class="stat-item">
        <div class="num small">{{ fmtMoney(summary.dividends.pending) }}</div>
        <div class="label">待发放分红</div>
      </div>
      <div class="stat-item">
        <div class="num small">{{ summary.policies.active_count }}</div>
        <div class="label">生效保单</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">申请中心</div>
      <div class="entry-grid">
        <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/farmer/apply?type=cert')">
          <div class="icon">🏅</div>
          <div class="name">品牌认证</div>
        </div>
        <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/farmer/apply?type=insurance')">
          <div class="icon">🛡️</div>
          <div class="name">保险投保</div>
        </div>
        <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/farmer/apply?type=loan')">
          <div class="icon">💰</div>
          <div class="name">贷款申请</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { showToast } from 'vant'
import api, { getAuth } from '../../api'
import { BANK_RESULT, RISK_LEVEL, CERT_STATUS, mapOf, tagTypeOf, fmtMoney } from '../../constants'

const auth = getAuth()
const userName = computed(() => (auth && auth.user && auth.user.real_name) || '农户')

const summary = ref({
  farmer: {},
  plots: { plot_count: 0, total_area_mu: 0 },
  policies: { policy_count: 0, active_count: 0 },
  latest_loan: null,
  dividends: { total: 0, pending: 0 },
})
const loan = computed(() => summary.value.latest_loan)
const riskText = computed(() => loan.value ? mapOf(RISK_LEVEL, loan.value.risk_level) : '')
const riskType = computed(() => loan.value ? tagTypeOf(RISK_LEVEL, loan.value.risk_level) : 'default')
const bankText = computed(() => loan.value ? mapOf(BANK_RESULT, loan.value.bank_result) : '-')
const certText = computed(() => {
  const s = summary.value.farmer.certification_status
  return s ? mapOf(CERT_STATUS, s) : ''
})
const certType = computed(() => tagTypeOf(CERT_STATUS, summary.value.farmer.certification_status || 'NONE'))

onMounted(async () => {
  try {
    summary.value = await api.get('/api/my/summary')
  } catch (e) {
    showToast(e.message)
  }
})
</script>
