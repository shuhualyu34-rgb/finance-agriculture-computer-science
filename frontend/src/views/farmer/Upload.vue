<template>
  <div class="page">
    <div class="hero" style="padding:14px 16px">
      <div class="hello">农事上传</div>
      <div class="sub">记录每一项农事，累积信用与溯源数据</div>
    </div>

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="plotName"
          is-link
          readonly
          label="选择地块"
          placeholder="请选择地块"
          :rules="[{ required: true, message: '请选择地块' }]"
          @click="showPlotPicker = true"
        />
        <van-field
          v-model="recordTypeName"
          is-link
          readonly
          label="记录类型"
          placeholder="请选择类型"
          :rules="[{ required: true, message: '请选择记录类型' }]"
          @click="showTypePicker = true"
        />
        <van-field
          v-model="form.record_date"
          is-link
          readonly
          label="记录日期"
          placeholder="请选择日期（不可晚于今天）"
          :rules="[{ required: true, message: '请选择日期' }]"
          @click="showCalendar = true"
        />
        <van-field
          v-model="form.description"
          rows="2"
          autosize
          type="textarea"
          label="描述"
          placeholder="简述本次农事操作"
          :rules="[{ required: true, message: '请填写描述' }]"
        />
        <van-field v-model="form.material_name" label="投入品名称" placeholder="如：有机肥（选填）" />
        <van-field v-model="form.material_amount" type="number" label="投入品用量" placeholder="如：50（选填）" />
        <van-field v-model="form.output_jin" type="number" label="产出(斤)" placeholder="收割/检测时填写（选填）" />
        <van-field label="现场照片" :rules="[]">
          <template #input>
            <van-uploader v-model="photos" multiple :after-read="afterRead" :max-count="6" />
          </template>
        </van-field>
      </van-cell-group>
      <div style="margin: 20px 16px">
        <van-button round block type="primary" native-type="submit" :loading="submitting" color="#4a7c59">
          提交记录
        </van-button>
      </div>
    </van-form>

    <van-popup v-model:show="showPlotPicker" position="bottom" round>
      <van-picker
        title="选择地块"
        :columns="plotColumns"
        @confirm="onPlotPicked"
        @cancel="showPlotPicker = false"
      />
    </van-popup>
    <van-popup v-model:show="showTypePicker" position="bottom" round>
      <van-picker
        title="记录类型"
        :columns="typeColumns"
        @confirm="onTypePicked"
        @cancel="showTypePicker = false"
      />
    </van-popup>
    <van-calendar
      v-model:show="showCalendar"
      :max-date="today"
      :min-date="minDate"
      @confirm="onDatePicked"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { showToast } from 'vant'
import api from '../../api'
import { RECORD_TYPES, mapOf } from '../../constants'

const today = new Date()
const minDate = new Date(2020, 0, 1)

const plots = ref([])
const plotColumns = computed(() =>
  plots.value.map((p) => ({ text: p.plot_name + '（' + p.area_mu + '亩）', value: p.id }))
)
const typeColumns = Object.keys(RECORD_TYPES).map((k) => ({ text: RECORD_TYPES[k], value: k }))

const showPlotPicker = ref(false)
const showTypePicker = ref(false)
const showCalendar = ref(false)

const plotName = ref('')
const recordTypeName = ref('')
const photos = ref([])
const submitting = ref(false)

function pad(n) { return String(n).padStart(2, '0') }
const form = ref({
  plot_id: null,
  record_type: '',
  record_date: today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate()),
  description: '',
  material_name: '',
  material_amount: '',
  output_jin: '',
})

onMounted(async () => {
  try {
    plots.value = await api.get('/api/my/plots')
  } catch (e) {
    showToast(e.message)
  }
})

function onPlotPicked({ selectedOptions }) {
  const opt = selectedOptions[0]
  form.value.plot_id = opt.value
  plotName.value = opt.text
  showPlotPicker.value = false
}
function onTypePicked({ selectedOptions }) {
  const opt = selectedOptions[0]
  form.value.record_type = opt.value
  recordTypeName.value = opt.text
  showTypePicker.value = false
}
function onDatePicked(d) {
  form.value.record_date = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
  showCalendar.value = false
}

async function afterRead(fileOrFiles) {
  const list = Array.isArray(fileOrFiles) ? fileOrFiles : [fileOrFiles]
  for (const f of list) {
    f.status = 'uploading'
    f.message = '上传中'
    try {
      const res = await api.upload(f.file)
      f.status = 'done'
      f.url = res.url
    } catch (e) {
      f.status = 'failed'
      f.message = '上传失败'
      showToast(e.message)
    }
  }
}

async function onSubmit() {
  if (new Date(form.value.record_date) > today) {
    showToast('记录日期不能晚于今天')
    return
  }
  const urls = photos.value.filter((p) => p.url).map((p) => p.url)
  submitting.value = true
  try {
    await api.post('/api/my/records', {
      plot_id: form.value.plot_id,
      record_type: form.value.record_type,
      record_date: form.value.record_date,
      description: form.value.description,
      material_name: form.value.material_name || undefined,
      material_amount: form.value.material_amount ? Number(form.value.material_amount) : undefined,
      output_jin: form.value.output_jin ? Number(form.value.output_jin) : undefined,
      photo_urls: urls.length ? urls : undefined,
    })
    showToast({ type: 'success', message: '提交成功' })
    form.value.description = ''
    form.value.material_name = ''
    form.value.material_amount = ''
    form.value.output_jin = ''
    photos.value = []
  } catch (e) {
    showToast(e.message)
  } finally {
    submitting.value = false
  }
}
</script>
