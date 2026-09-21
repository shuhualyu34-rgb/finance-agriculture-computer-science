<template>
  <div>
    <van-nav-bar title="丹邱优选商城" left-arrow @click-left="$router.back()" />
    <div class="page page-no-tab">
      <div class="hero" style="padding:14px 16px">
        <div class="hello">🌾 在线商城</div>
        <div class="sub">产地直供 · 每袋可溯源 · 消费享分红</div>
      </div>

      <van-pull-refresh v-model="refreshing" @refresh="load">
        <div v-if="!loading && products.length === 0" class="muted" style="text-align:center;padding:40px 0">暂无在售商品</div>
        <div class="card" v-for="p in products" :key="p.id" @click="openDetail(p)">
          <div class="card-title">
            <span style="flex:1;padding-right:8px">{{ p.product_name }}</span>
            <van-tag type="success" plain>{{ mapOf(PRODUCT_GRADE, p.product_grade) }}</van-tag>
          </div>
          <div class="row-line"><span class="k">规格</span><span>{{ p.specification }}</span></div>
          <div class="row-line"><span class="k">产地田块</span><span>{{ p.plot_name }}（{{ p.village }}）</span></div>
          <div class="row-line"><span class="k">种植农户</span><span>{{ p.farmer_name }}</span></div>
          <div class="row-line" style="align-items:flex-end">
            <span class="muted">库存 {{ p.stock }} 件</span>
            <span style="color:#c9a24b;font-weight:700;font-size:18px">¥{{ p.price }}</span>
          </div>
          <van-button size="small" round type="primary" color="#4a7c59" style="margin-top:8px" @click.stop="openDetail(p)">
            立即购买
          </van-button>
        </div>
      </van-pull-refresh>
    </div>

    <!-- 商品详情 + 下单弹层 -->
    <van-popup v-model:show="showDetail" position="bottom" round :style="{ maxHeight: '85%' }" closeable>
      <div class="page page-no-tab" v-if="current" style="padding-bottom:110px">
        <div class="card-title" style="padding:14px 16px 6px">
          {{ current.product_name }}
          <van-tag type="success" plain>{{ mapOf(PRODUCT_GRADE, current.product_grade) }}米</van-tag>
        </div>
        <div style="padding:0 16px">
          <div class="row-line"><span class="k">规格</span><span>{{ current.specification }}</span></div>
          <div class="row-line"><span class="k">单价</span><span style="color:#c9a24b;font-weight:700">¥{{ current.price }}</span></div>
          <div class="row-line"><span class="k">库存</span><span>{{ current.stock }} 件</span></div>
          <div class="row-line"><span class="k">产地田块</span><span>{{ current.plot_name }}（{{ current.village }}）</span></div>
          <div class="row-line"><span class="k">种植农户</span><span>{{ current.farmer_name }}</span></div>
          <div class="row-line">
            <span class="k">溯源码</span>
            <span style="color:#4a7c59" @click="goTrace(current.trace_code)">{{ current.trace_code }} 🔍</span>
          </div>

          <van-divider>填写订单</van-divider>
          <van-field v-model="quantity" type="digit" label="购买数量" placeholder="1">
            <template #button>件</template>
          </van-field>
          <van-field v-model="receiver" label="收货人" placeholder="请输入收货人姓名" />
          <van-field v-model="phone" type="tel" maxlength="11" label="联系电话" placeholder="请输入手机号" />
          <van-field
            v-model="address"
            rows="2"
            autosize
            type="textarea"
            label="收货地址"
            placeholder="省/市/区 + 详细地址"
          />
        </div>
      </div>
      <div v-if="current" style="position:absolute;left:0;right:0;bottom:0;padding:10px 16px;background:#fff;box-shadow:0 -2px 8px rgba(0,0,0,0.05)">
        <van-button round block type="primary" color="#4a7c59" :loading="submitting" @click="submitOrder">
          提交订单（合计 ¥{{ total }}）
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showDialog, showToast } from 'vant'
import api, { getAuth } from '../../api'
import { PRODUCT_GRADE, mapOf } from '../../constants'

const router = useRouter()
const products = ref([])
const loading = ref(true)
const refreshing = ref(false)

const showDetail = ref(false)
const current = ref(null)
const quantity = ref('1')
const receiver = ref('')
const phone = ref('')
const address = ref('')
const submitting = ref(false)

const auth = getAuth()
const total = computed(() => {
  const q = Number(quantity.value) || 0
  return current.value ? (q * current.value.price).toFixed(2) : '0.00'
})

async function load() {
  loading.value = true
  try {
    products.value = await api.get('/api/shop/products')
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}
onMounted(load)

function openDetail(p) {
  if (!auth || !auth.token) {
    showConfirmDialog({
      title: '请先登录',
      message: '登录后即可购买产地直供的丹邱丝苗米',
      confirmButtonText: '去登录',
    }).then(() => router.push('/consumer/login?redirect=/consumer/shop'))
      .catch(() => {})
    return
  }
  current.value = p
  quantity.value = '1'
  receiver.value = (auth.user && auth.user.real_name) || ''
  phone.value = (auth.user && auth.user.phone) || ''
  address.value = ''
  showDetail.value = true
}

function goTrace(code) {
  showDetail.value = false
  router.push({ path: '/consumer', query: { code } })
}

async function submitOrder() {
  const q = Number(quantity.value)
  if (!q || q < 1) return showToast('请输入正确的购买数量')
  if (!receiver.value) return showToast('请填写收货人')
  if (!phone.value) return showToast('请填写联系电话')
  if (!address.value) return showToast('请填写收货地址')
  submitting.value = true
  try {
    const order = await api.post('/api/shop/orders', {
      items: [{ product_id: current.value.id, quantity: q }],
      receiver: receiver.value,
      phone: phone.value,
      detail_address: address.value,
    })
    showDetail.value = false
    showConfirmDialog({
      title: '下单成功',
      message: '订单号 ' + order.order_no + '，合计 ¥' + order.total_amount + '，是否立即支付？',
      confirmButtonText: '立即支付',
      cancelButtonText: '稍后支付',
    })
      .then(async () => {
        try {
          await api.post('/api/shop/orders/' + order.id + '/pay')
          showDialog({
            title: '✅ 支付成功',
            message: '订单 ' + order.order_no + ' 已支付，等待发货。',
            confirmButtonText: '查看我的订单',
          }).then(() => {
            router.push('/consumer/orders')
          })
        } catch (e) {
          showToast(e.message)
        }
      })
      .catch(() => {
        router.push('/consumer/orders')
      })
  } catch (e) {
    showToast(e.status === 400 ? (e.message || '下单失败，请检查库存与收货信息') : e.message)
  } finally {
    submitting.value = false
  }
}
</script>
