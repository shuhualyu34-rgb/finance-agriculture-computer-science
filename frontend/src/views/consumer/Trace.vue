<template>
  <div class="page page-no-tab">
    <div class="hero">
      <div class="hello">🌾 丹邱丝苗米 · 溯源查询</div>
      <div class="sub">输入包装上的溯源码，查看这袋米的田间档案</div>
    </div>

    <div class="card">
      <van-field v-model="code" center clearable placeholder="请输入溯源码" style="padding:4px 0">
        <template #button>
          <van-button size="small" type="primary" color="#4a7c59" :loading="loading" @click="query">查 询</van-button>
        </template>
      </van-field>
      <van-button size="small" plain round color="#4a7c59" block style="margin-top:10px" @click="demo">
        一键演示（体验溯源码）
      </van-button>
    </div>

    <template v-if="trace">
      <div class="card">
        <div class="card-title">
          {{ trace.plot_name }}
          <van-tag type="success" plain>{{ mapOf(PRODUCT_GRADE, trace.product_grade) }}米</van-tag>
        </div>
        <div class="row-line"><span class="k">批次</span><span>{{ trace.batch_name }}</span></div>
        <div class="row-line"><span class="k">所在村</span><span>{{ trace.village }}</span></div>
        <div class="row-line"><span class="k">面积</span><span>{{ trace.area_mu }} 亩</span></div>
        <div class="row-line"><span class="k">品种</span><span>{{ trace.variety }}</span></div>
        <div class="row-line"><span class="k">种植农户</span><span>{{ trace.farmer_name }}</span></div>
      </div>

      <div class="card">
        <div class="card-title">卫星影像</div>
        <van-image
          v-if="usableImage(trace.satellite_image_url)"
          width="100%"
          height="160"
          fit="cover"
          :src="usableImage(trace.satellite_image_url)"
        />
        <div class="muted" style="margin-top:6px">地块坐标：{{ trace.longitude }}, {{ trace.latitude }}</div>
      </div>

      <div class="card">
        <div class="card-title">农事记录时间线</div>
        <div class="trace-tl">
          <div class="tl-item" v-for="(r, i) in sortedRecords" :key="i">
            <div style="font-weight:600;font-size:13px">
              {{ mapOf(RECORD_TYPES, r.record_type) }}
              <span class="muted" style="margin-left:8px">{{ r.record_date }}</span>
            </div>
            <div class="muted" style="margin-top:2px">{{ r.description }}</div>
            <div class="muted" v-if="r.material_name">投入品：{{ r.material_name }} {{ r.material_amount ?? '' }}</div>
            <div class="muted" v-if="r.output_jin != null">产出：{{ r.output_jin }} 斤</div>
          </div>
        </div>
      </div>
    </template>

    <div class="card entry-grid">
      <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/consumer/shop')">
        <div class="icon">🛒</div><div class="name">在线商城</div>
      </div>
      <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/consumer/orders')">
        <div class="icon">📦</div><div class="name">我的订单</div>
      </div>
      <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/consumer/adopt')">
        <div class="icon">🌱</div><div class="name">认养一块田</div>
      </div>
      <div class="entry-card" style="box-shadow:none;border:1px solid #eee" @click="$router.push('/consumer/mine')">
        <div class="icon">📋</div><div class="name">我的认养</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import api from '../../api'
import { RECORD_TYPES, PRODUCT_GRADE, mapOf, DEMO_TRACE_CODE } from '../../constants'

const route = useRoute()
const code = ref(typeof route.query.code === 'string' && route.query.code ? route.query.code : DEMO_TRACE_CODE)
const trace = ref(null)
const loading = ref(false)

function usableImage(url) {
  return typeof url === 'string' && url.trim() && !url.includes('danqiu.example.com') ? url : ''
}

onMounted(() => {
  if (code.value) query()
})

const sortedRecords = computed(() => {
  if (!trace.value) return []
  return [...(trace.value.production_records || [])].sort((a, b) => (a.record_date < b.record_date ? -1 : 1))
})

async function query() {
  if (!code.value) return showToast('请输入溯源码')
  loading.value = true
  trace.value = null
  try {
    trace.value = await api.get('/api/trace/' + encodeURIComponent(code.value.trim()))
  } catch (e) {
    showToast(e.status === 404 ? '溯源码不存在' : e.message)
  } finally {
    loading.value = false
  }
}

function demo() {
  code.value = DEMO_TRACE_CODE
  query()
}
</script>
