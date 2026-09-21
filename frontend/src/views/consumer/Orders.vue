<template>
  <div>
    <van-nav-bar title="我的订单" left-arrow @click-left="$router.back()" />
    <div class="page page-no-tab">
      <van-pull-refresh v-model="refreshing" @refresh="load">
        <div v-if="!loading && orders.length === 0" class="muted" style="text-align:center;padding:40px 0">
          暂无订单
          <div style="margin-top:12px">
            <van-button size="small" round type="primary" color="#4a7c59" @click="$router.push('/consumer/shop')">去商城逛逛</van-button>
          </div>
        </div>

        <div class="card" v-for="o in orders" :key="o.id">
          <div class="card-title">
            {{ o.order_no }}
            <van-tag :type="shopTagType(o.status)" plain>{{ mapOf(SHOP_ORDER_STATUS, o.status) }}</van-tag>
          </div>

          <van-steps :active="stepOf(o.status)" active-color="#4a7c59">
            <van-step>待支付</van-step>
            <van-step>已支付待发货</van-step>
            <van-step>已发货</van-step>
            <van-step>已完成</van-step>
          </van-steps>

          <div class="row-line" v-for="(it, i) in o.items" :key="i">
            <span class="k">{{ it.product_name }}</span>
            <span>{{ it.specification }} × {{ it.quantity }} = ¥{{ it.amount }}</span>
          </div>
          <div class="row-line">
            <span class="k">合计</span>
            <span style="color:#c9a24b;font-weight:700">¥{{ o.total_amount }}</span>
          </div>

          <template v-if="o.carrier || o.tracking_no">
            <div class="row-line"><span class="k">物流公司</span><span>{{ o.carrier || '-' }}</span></div>
            <div class="row-line"><span class="k">物流单号</span><span>{{ o.tracking_no || '-' }}</span></div>
          </template>
          <div v-if="o.address_snapshot" class="muted" style="margin-top:4px">
            收货：{{ addressText(o.address_snapshot) }}
          </div>
          <div class="muted" style="margin-top:4px">
            <span v-if="o.paid_at">支付于 {{ fmtDate(o.paid_at) }}</span>
            <span v-if="o.shipped_at"> · 发货于 {{ fmtDate(o.shipped_at) }}</span>
            <span v-if="o.completed_at"> · 完成于 {{ fmtDate(o.completed_at) }}</span>
          </div>

          <div style="margin-top:10px;display:flex;gap:8px">
            <van-button v-if="o.status === 'PENDING_PAYMENT'" size="small" round type="primary" color="#4a7c59" :loading="payingId === o.id" @click="pay(o)">
              模拟支付
            </van-button>
            <van-button v-if="o.status === 'SHIPPED'" size="small" round type="primary" color="#4a7c59" @click="confirm(o)">
              确认收货
            </van-button>
            <van-button size="small" plain round color="#4a7c59" @click="$router.push('/consumer/shop')">再买一点</van-button>
          </div>
        </div>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import api from '../../api'
import { SHOP_ORDER_STATUS, mapOf, fmtDate } from '../../constants'

const orders = ref([])
const loading = ref(true)
const refreshing = ref(false)
const payingId = ref(null)

function stepOf(status) {
  switch (status) {
    case 'PENDING_PAYMENT': return 0
    case 'PAID': return 1
    case 'SHIPPED': return 2
    case 'COMPLETED': return 3
    default: return 0
  }
}
function shopTagType(status) {
  switch (status) {
    case 'PENDING_PAYMENT': return 'warning'
    case 'PAID': return 'primary'
    case 'SHIPPED': return 'primary'
    case 'COMPLETED': return 'success'
    default: return 'default'
  }
}
function addressText(s) {
  if (!s) return ''
  if (typeof s === 'string') {
    try { s = JSON.parse(s) } catch { return s }
  }
  return [s.receiver, s.phone, s.detail_address || s.address].filter(Boolean).join(' ')
}

async function load() {
  loading.value = true
  try {
    orders.value = await api.get('/api/shop/my-orders')
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}
onMounted(load)

async function pay(o) {
  payingId.value = o.id
  try {
    const res = await api.post('/api/shop/orders/' + o.id + '/pay')
    showToast({ type: 'success', message: '支付成功，状态：' + mapOf(SHOP_ORDER_STATUS, res.status) })
    await load()
  } catch (e) {
    showToast(e.status === 409 ? '该订单当前状态不可支付' : e.message)
  } finally {
    payingId.value = null
  }
}

async function confirm(o) {
  try {
    const res = await api.post('/api/shop/orders/' + o.id + '/confirm')
    showToast({ type: 'success', message: '已确认收货，状态：' + mapOf(SHOP_ORDER_STATUS, res.status) })
    await load()
  } catch (e) {
    showToast(e.status === 409 ? '仅已发货的订单可确认收货' : e.message)
  }
}
</script>
