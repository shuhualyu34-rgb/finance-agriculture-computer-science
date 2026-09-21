<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="status" clearable placeholder="全部状态" style="width: 140px" @change="load">
        <el-option v-for="(t, k) in traceStatusMap" :key="k" :label="t" :value="k" />
      </el-select>
      <el-button type="primary" @click="visible = true">生成溯源码</el-button>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="code" label="溯源码" width="170" />
      <el-table-column prop="batch_name" label="批次" min-width="120" />
      <el-table-column label="等级" width="90">
        <template #default="{ row }">{{ gradeMap[row.product_grade] || row.product_grade }}</template>
      </el-table-column>
      <el-table-column prop="plot_name" label="地块" min-width="110" />
      <el-table-column prop="season_name" label="季别" min-width="100" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'">{{ traceStatusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="140">
        <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'ACTIVE'" link type="danger" @click="disable(row)">停用</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="生成溯源码" width="480px">
      <el-form label-width="90px">
        <el-form-item label="地块 ID">
          <el-input-number v-model="form.plot_id" :min="1" :max="500" style="width: 180px" />
          <div class="tip">请输入地块编号（1~500）。可在 H5 端通过溯源码查询获知地块 ID，或咨询管理员。</div>
        </el-form-item>
        <el-form-item label="批次名称">
          <el-input v-model="form.batch_name" placeholder="如：2025 春季头茬米" />
        </el-form-item>
        <el-form-item label="产品等级">
          <el-select v-model="form.product_grade" style="width: 160px">
            <el-option label="特级" value="SPECIAL" />
            <el-option label="一级" value="FIRST" />
            <el-option label="二级" value="SECOND" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'
import { fmtDateTime, traceStatusMap, gradeMap } from '../utils/format'

const status = ref('')
const rows = ref([])
const loading = ref(false)
const visible = ref(false)
const form = reactive({ plot_id: 1, batch_name: '', product_grade: 'FIRST' })
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/operator/trace-codes', { params: status.value ? { status: status.value } : {} })
  } finally { loading.value = false }
}

async function submit() {
  if (!form.batch_name) return ElMessage.warning('请填写批次名称')
  saving.value = true
  try {
    const res = await http.post('/api/operator/trace-codes', { ...form })
    ElMessage.success('生成成功，溯源码：' + res.code)
    visible.value = false
    load()
  } finally { saving.value = false }
}

async function disable(row) {
  await ElMessageBox.confirm('确认停用溯源码 ' + row.code + '？', '提示', { type: 'warning' })
  await http.put('/api/operator/trace-codes/' + row.id + '/disable')
  ElMessage.success('已停用')
  load()
}

onMounted(load)
</script>

<style scoped>
.tip { font-size: 12px; color: #909399; line-height: 1.5; margin-top: 4px; }
</style>
