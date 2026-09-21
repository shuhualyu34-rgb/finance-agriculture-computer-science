<template>
  <div class="page page-no-tab">
    <div class="hero" style="padding:14px 16px">
      <div class="hello">{{ userName }} 的认养</div>
      <div class="sub">电话：{{ phone }}</div>
    </div>
    <div style="margin-bottom:12px;display:flex;gap:8px">
      <van-button size="small" plain round color="#4a7c59" @click="$router.push('/consumer/adopt')">再去认养一块</van-button>
      <van-button size="small" plain round color="#999" @click="onLogout">退出登录</van-button>
    </div>

    <div class="card" v-for="(o, i) in orders" :key="o.id || i">
      <div class="card-title">
        {{ o.order_no }}
        <van-tag type="success" plain>{{ mapOf(ADOPTION_ORDER_STATUS, o.status) }}</van-tag>
      </div>
      <div class="row-line"><span class="k">地块</span><span>{{ o.plot_name }}({{ o.area_mu }} 亩 · {{ o.variety }})</span></div>
      <div class="row-line"><span class="k">种植农户</span><span>{{ o.farmer_name }}</span></div>
      <div class="row-line"><span class="k">所在村</span><span>{{ o.village }}</span></div>
      <div class="row-line"><span class="k">认养动态</span><span>认养后新增农事记录 {{ o.updates_since_adopted }} 条</span></div>
      <div class="row-line"><span class="k">费用</span><span style="color:#4a7c59;font-weight:700">¥{{ o.fee }}</span></div>
      <div class="muted" style="margin-top:4px">认养于 {{ fmtDate(o.started_at) }}</div>
    </div>
    <van-empty v-if="orders.length === 0 && !loading" description="还没有认养记录,去认养一块田吧" image-size="64">
      <van-button round type="primary" color="#4a7c59" size="small" @click="$router.push('/consumer/adopt')">
        去认养
      </van-button>
    </van-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, getAuth, logout } from '../../api'
import { ADOPTION_ORDER_STATUS, mapOf, fmtDate } from '../../constants'

const auth = getAuth()
const userName = computed(() => (auth && auth.user && auth.user.real_name) || '我')
const phone = computed(() => (auth && auth.user && auth.user.phone) || '-')
const router = useRouter()
const orders = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    orders.value = await api.get('/api/my/adoptions')
  } catch (e) {
    orders.value = []
  } finally {
    loading.value = false
  }
})

function onLogout() {
  logout()
  router.replace('/consumer/login')
}
</script>
