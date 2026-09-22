<template>
  <div>
    <van-nav-bar title="田块详情" left-arrow @click-left="$router.back()" />
    <div class="page page-no-tab" v-if="plot">
      <div class="card">
        <div class="card-title">
          {{ plot.plot_name }}
          <van-tag :type="tagTypeOf(CERT_STATUS, plot.cert_status || 'NONE')">{{ mapOf(CERT_STATUS, plot.cert_status || 'NONE') }}</van-tag>
        </div>
        <div class="row-line"><span class="k">地块编号</span><span>{{ plot.plot_code }}</span></div>
        <div class="row-line"><span class="k">所在村</span><span>{{ plot.village }}</span></div>
        <div class="row-line"><span class="k">面积</span><span>{{ plot.area_mu }} 亩</span></div>
        <div class="row-line"><span class="k">品种</span><span>{{ plot.variety }}</span></div>
        <div class="row-line"><span class="k">坐标</span><span>{{ plot.longitude }}, {{ plot.latitude }}</span></div>
      </div>

      <div class="card">
        <div class="card-title">
          卫星地图
          <van-tag type="success" plain>丹邱村定位</van-tag>
        </div>
        <div ref="mapEl" class="plot-map"></div>
        <div class="map-hint">可缩放、拖动地图；地图仅显示丹邱村公共定位</div>
      </div>

      <div class="card">
        <div class="card-title">农事记录时间线</div>
        <div v-if="records.length === 0" class="muted">暂无记录</div>
        <div class="trace-tl">
          <div class="tl-item" v-for="r in records" :key="r.id">
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
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import api from '../../api'
import { CERT_STATUS, RECORD_TYPES, mapOf, tagTypeOf } from '../../constants'

const route = useRoute()
const plot = ref(null)
const records = ref([])
const mapEl = ref(null)
let mapInstance

function initMap() {
  if (!plot.value || !mapEl.value || mapInstance) return
  const lat = Number(plot.value.latitude)
  const lng = Number(plot.value.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return
  mapInstance = L.map(mapEl.value, { zoomControl: true, attributionControl: true }).setView([lat, lng], 16)

  const satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19, attribution: 'Tiles © Esri' },
  ).addTo(mapInstance)
  const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '© OpenStreetMap contributors',
  })
  L.control.layers({ 卫星影像: satellite, 标准地图: street }, undefined, { position: 'topright' }).addTo(mapInstance)

  const villageMarker = L.marker([23.2987580, 113.7506230]).addTo(mapInstance)
    .bindPopup('丹邱村')
  mapInstance.setView([23.2987580, 113.7506230], 14)
  villageMarker.openPopup()
}

onMounted(async () => {
  const id = route.params.id
  try {
    const plots = await api.get('/api/my/plots')
    plot.value = plots.find((p) => String(p.id) === String(id)) || null
    requestAnimationFrame(initMap)
    records.value = await api.get('/api/my/records?plot_id=' + id)
    records.value.sort((a, b) => (a.record_date < b.record_date ? -1 : 1))
  } catch (e) {
    showToast(e.message)
  }
})
</script>

<style scoped>
.plot-map {
  width: 100%;
  height: 280px;
  border-radius: 8px;
  overflow: hidden;
  background: #e8eee9;
}
.map-hint {
  margin-top: 8px;
  color: #8a9690;
  font-size: 12px;
}
</style>
