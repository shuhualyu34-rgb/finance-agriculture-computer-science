<template>
  <div>
    <van-nav-bar title="申请中心" left-arrow @click-left="$router.back()" />
    <div class="page page-no-tab">
      <div class="entry-grid">
        <div class="entry-card" :style="active === 'cert' ? 'border:1.5px solid #4a7c59' : ''" @click="active = 'cert'">
          <div class="icon">🏅</div><div class="name">品牌认证</div><div class="desc">区域公用品牌认证</div>
        </div>
        <div class="entry-card" :style="active === 'insurance' ? 'border:1.5px solid #4a7c59' : ''" @click="active = 'insurance'">
          <div class="icon">🛡️</div><div class="name">保险投保</div><div class="desc">水稻种植保险</div>
        </div>
        <div class="entry-card" :style="active === 'loan' ? 'border:1.5px solid #4a7c59' : ''" @click="active = 'loan'">
          <div class="icon">💰</div><div class="name">贷款申请</div><div class="desc">地块抵押授信建议</div>
        </div>
      </div>

      <!-- 品牌认证 -->
      <div class="card" v-if="active === 'cert'">
        <div class="card-title">品牌认证申请</div>
        <van-field v-model="certPlotName" is-link readonly label="选择地块" placeholder="请选择地块" @click="openPicker('cert')" />
        <van-field v-model="certNote" rows="2" autosize type="textarea" label="备注" placeholder="补充说明（选填）" style="margin-top:8px" />
        <van-button round block type="primary" color="#4a7c59" style="margin-top:14px" :loading="submitting" @click="submitCert">提交认证申请</van-button>
        <div class="muted" style="margin-top:8px">提交后进入人工审核，同地块待审期间不可重复申请。</div>
      </div>

      <!-- 保险投保 -->
      <div class="card" v-if="active === 'insurance'">
        <div class="card-title">保险投保（特色农险产品）</div>
        <select v-model="productId" class="native-select">
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.product_name }}</option>
        </select>
        <div v-if="selectedProduct" class="muted" style="margin:8px 0">{{ selectedProduct.description }}</div>
        <van-field v-model="insPlotName" is-link readonly label="选择地块" placeholder="请选择地块" @click="openPicker('insurance')" />
        <template v-if="quote">
          <div class="section-gap"></div>
          <div class="row-line"><span class="k">保额</span><span style="font-weight:700">{{ fmtMoney(quote.insured_amount) }}</span></div>
          <div class="row-line"><span class="k">总保费</span><span>{{ fmtMoney(quote.total_premium) }}</span></div>
          <div class="row-line"><span class="k">政府补贴</span><span style="color:#d97706">-{{ fmtMoney(quote.government_subsidy) }}</span></div>
          <div class="row-line"><span class="k">个人自缴</span><span style="color:#4a7c59;font-weight:700">{{ fmtMoney(quote.farmer_premium) }}</span></div>
        </template>
        <van-button round block type="primary" color="#4a7c59" style="margin-top:14px" :loading="submitting" @click="submitInsurance">
          {{ quote ? '已投保，再次试算请点击' : '试算并投保' }}
        </van-button>
        <div class="muted" style="margin-top:8px">点击后调用后端试算接口并完成投保，展示保额/保费/补贴明细。</div>
      </div>

      <!-- 贷款申请 -->
      <div class="card" v-if="active === 'loan'">
        <div class="card-title">贷款授信申请</div>
        <van-field v-model="loanPlotName" is-link readonly label="选择地块" placeholder="请选择地块" @click="openPicker('loan')" />
        <van-field v-model="loanPurpose" label="贷款用途" placeholder="如：购买农资（选填）" style="margin-top:8px" />
        <template v-if="loanResult">
          <div class="section-gap"></div>
          <div class="row-line"><span class="k">系统建议额度</span><span style="color:#4a7c59;font-weight:700;font-size:16px">{{ fmtMoney(loanResult.suggested_amount) }}</span></div>
          <div class="row-line">
            <span class="k">风险评级</span>
            <van-tag :type="tagTypeOf(RISK_LEVEL, loanResult.risk_level)">{{ mapOf(RISK_LEVEL, loanResult.risk_level) }}</van-tag>
          </div>
          <div class="row-line"><span class="k">已品牌认证</span><span>{{ loanResult.basis.certified ? '✅ 是' : '❌ 否' }}</span></div>
          <div class="row-line"><span class="k">有农业保险</span><span>{{ loanResult.basis.has_insurance ? '✅ 是' : '❌ 否' }}</span></div>
          <div class="row-line"><span class="k">资料完整性</span><span>{{ loanResult.basis.profile_complete ? '✅ 完整' : '❌ 待完善' }}</span></div>
          <van-notice-bar left-icon="info-o" text="额度建议仅供参考，最终以银行审批结果为准" style="margin-top:8px;border-radius:8px" />
        </template>
        <van-button round block type="primary" color="#4a7c59" style="margin-top:14px" :loading="submitting" @click="submitLoan">提交申请</van-button>
      </div>
    </div>

    <van-popup v-model:show="showPicker" position="bottom" round>
      <van-picker title="选择地块" :columns="plotColumns" @confirm="onPicked" @cancel="showPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import api from '../../api'
import { RISK_LEVEL, mapOf, tagTypeOf, fmtMoney } from '../../constants'

const route = useRoute()
const active = ref(route.query.type === 'insurance' || route.query.type === 'loan' ? route.query.type : 'cert')

const plots = ref([])
const plotColumns = computed(() => plots.value.map((p) => ({ text: p.plot_name + '（' + p.area_mu + '亩）', value: p.id })))

const showPicker = ref(false)
const pickerTarget = ref('cert')
const certPlotName = ref('')
const insPlotName = ref('')
const loanPlotName = ref('')
const certPlotId = ref(null)
const insPlotId = ref(null)
const loanPlotId = ref(null)
const certNote = ref('')
const loanPurpose = ref('')
const quote = ref(null)
const products = ref([])
const productId = ref(1)
const loanResult = ref(null)
const submitting = ref(false)

onMounted(async () => {
  try {
    plots.value = await api.get('/api/my/plots')
    products.value = await api.get('/api/my/insurance-products')
    if (products.value.length) productId.value = products.value[0].id
  } catch (e) {
    showToast(e.message)
  }
})

function openPicker(target) {
  pickerTarget.value = target
  showPicker.value = true
}

const selectedProduct = computed(() => products.value.find((p) => p.id === Number(productId.value)))
function onPicked({ selectedOptions }) {
  const opt = selectedOptions[0]
  if (pickerTarget.value === 'cert') { certPlotId.value = opt.value; certPlotName.value = opt.text }
  else if (pickerTarget.value === 'insurance') { insPlotId.value = opt.value; insPlotName.value = opt.text }
  else { loanPlotId.value = opt.value; loanPlotName.value = opt.text }
  showPicker.value = false
}

async function submitCert() {
  if (!certPlotId.value) return showToast('请选择地块')
  submitting.value = true
  try {
    await api.post('/api/my/certifications', { plot_id: certPlotId.value, note: certNote.value || '' })
    showToast({ type: 'success', message: '已提交，待审核' })
    certNote.value = ''
  } catch (e) {
    if (e.status === 409) showToast('该地块已有待审核的认证申请')
    else showToast(e.message)
  } finally {
    submitting.value = false
  }
}

async function submitInsurance() {
  if (!insPlotId.value) return showToast('请选择地块')
  submitting.value = true
  try {
    const res = await api.post('/api/my/insurance', { plot_id: insPlotId.value, product_id: Number(productId.value) })
    quote.value = res.quote
    showConfirmDialog({
      title: '投保成功',
      message: '保额 ' + fmtMoney(res.quote.insured_amount) + '，自缴 ' + fmtMoney(res.quote.farmer_premium) + '，保单已生成。',
      confirmButtonText: '知道了',
      showCancelButton: false,
    })
  } catch (e) {
    showToast(e.message)
  } finally {
    submitting.value = false
  }
}

async function submitLoan() {
  if (!loanPlotId.value) return showToast('请选择地块')
  submitting.value = true
  try {
    const res = await api.post('/api/my/loans', { plot_id: loanPlotId.value, purpose_note: loanPurpose.value || undefined })
    loanResult.value = res
    showToast({ type: 'success', message: '已提交' })
  } catch (e) {
    showToast(e.message)
  } finally {
    submitting.value = false
  }
}
</script>
