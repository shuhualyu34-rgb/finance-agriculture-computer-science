<template>
  <div class="page">
    <div class="hero" style="padding:14px 16px">
      <div class="hello">{{ userName }}</div>
      <div class="sub">电话：{{ phone }}</div>
    </div>
    <div class="card" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer" @click="$router.push('/farmer/income')">
      <div>
        <div style="font-weight:600;font-size:14px">💰 我的收入</div>
        <div class="muted" style="margin-top:2px">地租 · 工资 · 品牌溢价 · 平台销售分红</div>
      </div>
      <van-icon name="arrow" color="#999" />
    </div>
    <div class="card" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-weight:600;font-size:14px">👵 关怀模式</div>
        <div class="muted" style="margin-top:2px">大字显示 · 右下角🔊朗读本页</div>
      </div>
      <van-switch :model-value="careMode" size="24px" active-color="#4a7c59" @update:model-value="onCareToggle" />
    </div>
    <div style="margin-bottom:12px">
      <van-button size="small" plain round color="#4a7c59" @click="onLogout">退出登录</van-button>
    </div>

    <van-tabs v-model:active="tab" sticky color="#4a7c59" animated>
      <van-tab title="贷款">
        <div class="card" v-for="l in loans" :key="l.id">
          <div class="card-title">
            {{ l.application_no }}
            <van-tag :type="tagTypeOf(BANK_RESULT_TAG, l.bank_result)">{{ mapOf(BANK_RESULT, l.bank_result) }}</van-tag>
          </div>
          <div class="row-line"><span class="k">地块</span><span>{{ l.plot_name }}</span></div>
          <div class="row-line"><span class="k">面积</span><span>{{ l.area_mu }} 亩</span></div>
          <div class="row-line"><span class="k">建议额度</span><span>{{ fmtMoney(l.suggested_amount) }}</span></div>
          <div class="row-line"><span class="k">风险评级</span><span>{{ mapOf(RISK_LEVEL, l.risk_level) }}</span></div>
          <div class="row-line" v-if="l.bank_note"><span class="k">银行备注</span><span>{{ l.bank_note }}</span></div>
          <div class="muted" style="margin-top:4px">申请于 {{ fmtDate(l.applied_at) }}</div>
        </div>
        <van-empty v-if="!loading && loans.length === 0" description="暂无贷款记录" image-size="64" />
      </van-tab>

      <van-tab title="保单">
        <div class="card" v-for="p in policies" :key="p.id">
          <div class="card-title">
            {{ p.policy_no }}
            <van-tag type="success" plain>{{ mapOf(POLICY_STATUS, p.status) }}</van-tag>
          </div>
          <div class="row-line"><span class="k">地块</span><span>{{ p.plot_name }}</span></div>
          <div class="row-line"><span class="k">产品</span><span>{{ p.product_name }}</span></div>
          <div class="row-line"><span class="k">投保面积</span><span>{{ p.insured_area_mu }} 亩</span></div>
          <div class="row-line"><span class="k">保额</span><span>{{ fmtMoney(p.insured_amount) }}</span></div>
          <div class="row-line"><span class="k">自缴保费</span><span>{{ fmtMoney(p.farmer_premium) }}</span></div>
        </div>
        <van-empty v-if="!loading && policies.length === 0" description="暂无保单" image-size="64" />
      </van-tab>

      <van-tab title="理赔">
        <div class="card" v-for="c in claims" :key="c.id">
          <div class="card-title">
            {{ c.claim_no }}
            <van-tag :type="c.status === 'APPROVED' ? 'success' : c.status === 'REJECTED' ? 'danger' : 'warning'" plain>
              {{ mapOf(CLAIM_STATUS, c.status) }}
            </van-tag>
          </div>
          <div class="row-line"><span class="k">保单号</span><span>{{ c.policy_no }}</span></div>
          <div class="row-line"><span class="k">地块</span><span>{{ c.plot_name }}</span></div>
          <div class="row-line"><span class="k">灾害描述</span><span>{{ c.disaster_note }}</span></div>
          <div class="row-line"><span class="k">受损率</span><span>{{ c.disaster_rate }}%</span></div>
          <div class="row-line"><span class="k">理赔金额</span><span style="color:#4a7c59;font-weight:700">{{ fmtMoney(c.claim_amount) }}</span></div>
        </div>
        <van-empty v-if="!loading && claims.length === 0" description="暂无理赔记录" image-size="64" />
      </van-tab>

      <van-tab title="分红">
        <div class="card" v-for="d in dividends" :key="d.id">
          <div class="card-title">
            {{ d.order_no }}
            <van-tag :type="d.status === 'PAID' ? 'success' : 'warning'" plain>{{ mapOf(DIVIDEND_STATUS, d.status) }}</van-tag>
          </div>
          <div class="row-line"><span class="k">地块</span><span>{{ d.plot_name }}</span></div>
          <div class="row-line"><span class="k">订单金额</span><span>{{ fmtMoney(d.base_amount) }}</span></div>
          <div class="row-line"><span class="k">分红比例</span><span>{{ d.dividend_rate }}%</span></div>
          <div class="row-line"><span class="k">分红金额</span><span style="color:#4a7c59;font-weight:700">{{ fmtMoney(d.dividend_amount) }}</span></div>
        </div>
        <van-empty v-if="!loading && dividends.length === 0" description="暂无分红明细" image-size="64" />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api, { getAuth, logout } from '../../api'
import { careMode, toggleCare, speak } from '../../care'
import {
  BANK_RESULT, RISK_LEVEL, POLICY_STATUS, CLAIM_STATUS, DIVIDEND_STATUS,
  mapOf, tagTypeOf, fmtMoney, fmtDate,
} from '../../constants'

const BANK_RESULT_TAG = { PENDING: 'warning', APPROVED: 'success', REJECTED: 'danger' }

const auth = getAuth()
const userName = computed(() => (auth && auth.user && auth.user.real_name) || '我的')
const phone = computed(() => (auth && auth.user && auth.user.phone) || '-')

const router = useRouter()
const tab = ref(0)
const loans = ref([])
const policies = ref([])
const claims = ref([])
const dividends = ref([])
const loading = ref(true)

function onLogout() {
  logout()
  router.replace('/farmer/login')
}

function onCareToggle(on) {
  toggleCare(on)
  if (on) speak('关怀模式已开启，字变大了。点击右下角喇叭按钮，可以朗读本页内容。')
}

onMounted(async () => {
  try {
    const [l, p, c, d] = await Promise.all([
      api.get('/api/my/loans'),
      api.get('/api/my/policies'),
      api.get('/api/my/claims'),
      api.get('/api/my/dividends'),
    ])
    loans.value = l
    policies.value = p
    claims.value = c
    dividends.value = d
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
  }
})
</script>
