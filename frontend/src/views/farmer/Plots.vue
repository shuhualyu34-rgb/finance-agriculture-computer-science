<template>
  <div class="page">
    <div class="hero" style="padding:14px 16px">
      <div class="hello">我的田块</div>
      <div class="sub">点击田块查看农事记录与卫星图</div>
    </div>
    <van-pull-refresh v-model="refreshing" @refresh="load">
      <div v-if="!loading && plots.length === 0" class="muted" style="text-align:center;padding:40px 0">暂无田块数据</div>
      <div class="card" v-for="p in plots" :key="p.id" @click="$router.push('/farmer/plots/' + p.id)">
        <div class="card-title">
          {{ p.plot_name }}
          <van-tag :type="tagTypeOf(CERT_STATUS, p.cert_status || 'NONE')">{{ mapOf(CERT_STATUS, p.cert_status || 'NONE') }}</van-tag>
        </div>
        <div class="row-line"><span class="k">地块编号</span><span>{{ p.plot_code }}</span></div>
        <div class="row-line"><span class="k">所在村</span><span>{{ p.village }}</span></div>
        <div class="row-line"><span class="k">面积</span><span>{{ p.area_mu }} 亩</span></div>
        <div class="row-line"><span class="k">品种</span><span>{{ p.variety }}</span></div>
      </div>
    </van-pull-refresh>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import api from '../../api'
import { CERT_STATUS, mapOf, tagTypeOf } from '../../constants'

const plots = ref([])
const loading = ref(false)
const refreshing = ref(false)

async function load() {
  loading.value = true
  try {
    plots.value = await api.get('/api/my/plots')
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}
onMounted(load)
</script>
