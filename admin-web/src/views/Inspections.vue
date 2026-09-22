<template>
  <div class="page">
    <el-card style="max-width: 720px; margin-bottom: 16px">
      <template #header>实地巡检采集</template>
      <el-form :model="form" label-width="110px" inline="false">
        <el-form-item label="地块 ID">
          <el-input-number v-model="form.plot_id" :min="1" :max="500" />
          <span class="tip">请输入地块编号（1~500）</span>
        </el-form-item>
        <el-form-item label="巡检日期">
          <el-date-picker v-model="form.inspection_date" type="date" value-format="YYYY-MM-DD" style="width: 180px" />
        </el-form-item>
        <el-form-item label="巡检结果">
          <el-radio-group v-model="form.result">
            <el-radio label="PASS">合格</el-radio>
            <el-radio label="WARNING">预警</el-radio>
            <el-radio label="FAIL">不合格</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="实测面积(亩)">
          <el-input-number v-model="form.actual_area_mu" :min="0" :step="0.1" :precision="2" placeholder="选填" />
          <span class="tip">填写后与申报面积交叉核验，差异 &gt; 20% 自动转为预警</span>
        </el-form-item>
        <el-form-item label="差异说明">
          <el-input v-model="form.difference_note" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
        <el-form-item label="需要整改">
          <el-switch v-model="form.rectification_required" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">提交采集</el-button>
        </el-form-item>
      </el-form>
      <el-alert v-if="lastResult" :title="lastResult.text" :type="lastResult.type" show-icon style="margin-top: 8px" />
    </el-card>

    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="plot_id" label="地块ID" width="80" />
      <el-table-column prop="plot_code" label="地块编码" width="140" />
      <el-table-column prop="plot_name" label="地块名称" min-width="120" />
      <el-table-column prop="village" label="村组" min-width="110" />
      <el-table-column prop="inspection_date" label="巡检日期" width="110" />
      <el-table-column label="结果" width="90">
        <template #default="{ row }">
          <el-tag :type="{ PASS: 'success', WARNING: 'warning', FAIL: 'danger' }[row.result] || 'info'">
            {{ inspectionResultMap[row.result] || row.result }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="difference_note" label="差异说明" min-width="200">
        <template #default="{ row }">
          <span :style="row.difference_note && row.difference_note.includes('面积交叉核验') ? 'color:#e6a23c;font-weight:bold' : ''">
            {{ row.difference_note || '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="需整改" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.rectification_required" type="danger" size="small">需整改</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="inspector_name" label="巡检员" width="110" />
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { inspectionResultMap } from '../utils/format'

const form = reactive({
  plot_id: 1,
  inspection_date: new Date().toISOString().slice(0, 10),
  result: 'PASS',
  actual_area_mu: undefined,
  difference_note: '',
  rectification_required: false
})
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const lastResult = ref(null)

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/government/inspections')
  } finally { loading.value = false }
}

async function submit() {
  saving.value = true
  lastResult.value = null
  try {
    const body = { ...form }
    if (body.actual_area_mu === undefined || body.actual_area_mu === null) delete body.actual_area_mu
    const res = await http.post('/api/government/inspections', body)
    if (res.auto_warning) {
      lastResult.value = { type: 'warning', text: '面积差异超 20%，系统自动转为预警：' + (res.note || '') }
    } else {
      lastResult.value = { type: 'success', text: '采集成功，结果：' + inspectionResultMap[res.result] }
    }
    ElMessage.success('采集成功')
    load()
  } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.tip { font-size: 12px; color: #909399; margin-left: 8px; }
</style>
