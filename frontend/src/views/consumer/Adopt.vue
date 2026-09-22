<template>
  <div class="page">
    <div class="hero" style="padding:14px 16px">
      <div class="hello">田块认养</div>
      <div class="sub">认养一块丝苗米田，秋收寄新米，还能享消费分红</div>
    </div>

    <div v-if="!loading && plots.length === 0" class="muted" style="text-align:center;padding:40px 0">暂无可认养田块</div>

    <div class="card" v-for="p in plots" :key="p.id">
      <div class="card-title">
        {{ p.plot_name }}
        <van-tag color="#4a7c59" plain>¥{{ p.adoption_fee }}/季</van-tag>
      </div>
      <div class="row-line"><span class="k">农户</span><span>{{ p.farmer_name }}</span></div>
      <div class="row-line"><span class="k">所在村</span><span>{{ p.village }}</span></div>
      <div class="row-line"><span class="k">面积</span><span>{{ p.area_mu }} 亩</span></div>
      <div class="row-line"><span class="k">品种</span><span>{{ p.variety }}</span></div>
      <div class="row-line"><span class="k">已认养</span><span>{{ p.adopted_count }} 人</span></div>
      <van-image
        v-if="usableImage(p.satellite_image_url)"
        width="100%"
        height="120"
        fit="cover"
        :src="usableImage(p.satellite_image_url)"
        style="margin-top:8px;border-radius:8px"
      />
      <van-button round block type="primary" color="#4a7c59" style="margin-top:12px" @click="adopt(p)">
        认养这块田
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { showConfirmDialog, showDialog, showToast } from 'vant'
import api from '../../api'

const plots = ref([])
const loading = ref(true)

function usableImage(url) {
  return typeof url === 'string' && url.trim() && !url.includes('danqiu.example.com') ? url : ''
}

onMounted(async () => {
  try {
    plots.value = await api.get('/api/adoption/plots')
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
  }
})

function adopt(p) {
  showConfirmDialog({
    title: '确认认养',
    message: '认养「' + p.plot_name + '」，支付 ¥' + p.adoption_fee + '（模拟支付）',
    confirmButtonText: '确认支付',
    cancelButtonText: '再想想',
  })
    .then(async () => {
      try {
        const res = await api.post('/api/adoption/orders', { plot_id: p.id })
        saveLocalOrder(res, p)
        showDialog({
          title: '🎉 认养成功',
          message: '认养单号 ' + res.order_no + '，地块：' + p.plot_name + '，支付：¥' + res.fee,
          confirmButtonText: '去看看我的认养',
        }).then(() => {
          window.location.href = '/consumer/mine'
        })
      } catch (e) {
        showToast(e.status === 409 ? '您已认养过这块田啦' : e.message)
      }
    })
    .catch(() => {})
}

function saveLocalOrder(res, p) {
  try {
    const list = JSON.parse(localStorage.getItem('dq_adoptions') || '[]')
    list.unshift({
      order_no: res.order_no,
      plot_name: p.plot_name,
      plot_code: p.plot_code,
      village: p.village,
      fee: res.fee,
      status: res.status,
      paid: res.paid,
      created_at: new Date().toISOString(),
    })
    localStorage.setItem('dq_adoptions', JSON.stringify(list))
  } catch { /* ignore */ }
}
</script>
