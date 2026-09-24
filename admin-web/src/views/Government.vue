<template>
  <div class="page government-page">
    <div class="toolbar">
      <el-button type="primary" @click="load" :loading="loading">刷新数据</el-button>
    </div>

    <el-row :gutter="12" class="stats">
      <el-col v-for="item in statItems" :key="item.key" :span="4">
        <el-card shadow="never" class="stat-card">
          <el-statistic :title="item.label" :value="cards[item.key] || 0" />
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" class="content-tabs">
      <el-tab-pane label="异常预警" name="alerts">
        <el-table :data="alerts" border stripe v-loading="loading">
          <el-table-column label="等级" width="90">
            <template #default="{ row }"><el-tag :type="row.level === 'FAIL' ? 'danger' : 'warning'">{{ levelMap[row.level] || row.level }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="alert_type" label="来源" width="130" />
          <el-table-column prop="plot_name" label="地块" min-width="150" />
          <el-table-column prop="owner_name" label="农户" width="100" />
          <el-table-column prop="detail" label="问题描述" min-width="220" />
          <el-table-column prop="occurred_at" label="发生时间" width="140" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="现场核验" name="inspections">
        <div class="toolbar"><el-button type="primary" @click="openInspection">新增核验记录</el-button></div>
        <el-table :data="inspections" border stripe v-loading="loading">
          <el-table-column prop="inspection_date" label="核验日期" width="120" />
          <el-table-column prop="plot_name" label="地块" min-width="160" />
          <el-table-column prop="village" label="村组" width="110" />
          <el-table-column prop="inspector_name" label="核验员" width="110" />
          <el-table-column label="结果" width="90"><template #default="{ row }"><el-tag :type="row.result === 'PASS' ? 'success' : row.result === 'FAIL' ? 'danger' : 'warning'">{{ levelMap[row.result] || row.result }}</el-tag></template></el-table-column>
          <el-table-column prop="difference_note" label="备注" min-width="220" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="监管报表" name="reports">
        <el-table :data="reports" border stripe v-loading="loading">
          <el-table-column label="类型" width="100"><template #default="{ row }">{{ reportTypeMap[row.report_type] || row.report_type }}</template></el-table-column>
          <el-table-column prop="report_period" label="周期" width="120" />
          <el-table-column label="摘要" min-width="260"><template #default="{ row }">{{ row.content?.summary || '-' }}</template></el-table-column>
          <el-table-column label="状态" width="110"><template #default="{ row }"><el-tag :type="row.status === 'CONFIRMED' ? 'success' : row.status === 'DRAFT' ? 'warning' : 'info'">{{ reportStatusMap[row.status] || row.status }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="120"><template #default="{ row }"><el-button v-if="row.status === 'DRAFT'" link type="primary" @click="confirmReport(row)">确认报表</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="inspectionVisible" title="新增现场核验" width="520px">
      <el-form :model="inspection" label-width="100px">
        <el-form-item label="核验地块"><el-select v-model="inspection.plot_id" filterable placeholder="请选择地块" style="width:100%"><el-option v-for="p in plots" :key="p.id" :label="`${p.plot_name}（${p.farmer_name}）`" :value="p.id" /></el-select></el-form-item>
        <el-form-item label="核验日期"><el-date-picker v-model="inspection.inspection_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="核验结果"><el-radio-group v-model="inspection.result"><el-radio label="PASS">通过</el-radio><el-radio label="WARNING">预警</el-radio><el-radio label="FAIL">不通过</el-radio></el-radio-group></el-form-item>
        <el-form-item label="需要整改"><el-switch v-model="inspection.rectification_required" /></el-form-item>
        <el-form-item label="问题备注"><el-input v-model="inspection.difference_note" type="textarea" :rows="3" placeholder="记录面积、农事、品控等现场差异" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="inspectionVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveInspection">保存记录</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'

const loading = ref(false)
const saving = ref(false)
const activeTab = ref('alerts')
const cards = ref({})
const alerts = ref([])
const inspections = ref([])
const reports = ref([])
const plots = ref([])
const inspectionVisible = ref(false)
const inspection = reactive({ plot_id: null, inspection_date: '', result: 'PASS', rectification_required: false, difference_note: '' })
const statItems = [
  { key: 'farmer_count', label: '农户数' }, { key: 'active_plot_count', label: '有效地块' },
  { key: 'warning_count', label: '异常核验' }, { key: 'correction_count', label: '待整改记录' },
  { key: 'draft_report_count', label: '待确认报表' }, { key: 'pending_cert_count', label: '待审认证' }
]
const levelMap = { PASS: '通过', WARNING: '预警', FAIL: '不通过' }
const reportTypeMap = { WEEKLY: '周报', MONTHLY: '月报', QUARTERLY: '季报' }
const reportStatusMap = { DRAFT: '草稿', CONFIRMED: '已确认', ARCHIVED: '已归档' }

async function load() {
  loading.value = true
  try {
    const data = await http.get('/api/government/workbench')
    cards.value = data.cards; alerts.value = data.alerts; inspections.value = data.inspections; reports.value = data.reports
  } finally { loading.value = false }
}
async function openInspection() {
  plots.value = await http.get('/api/government/plots')
  Object.assign(inspection, { plot_id: null, inspection_date: new Date().toISOString().slice(0, 10), result: 'PASS', rectification_required: false, difference_note: '' })
  inspectionVisible.value = true
}
async function saveInspection() {
  saving.value = true
  try { await http.post('/api/government/inspections', inspection); ElMessage.success('核验记录已保存'); inspectionVisible.value = false; await load() }
  finally { saving.value = false }
}
async function confirmReport(row) {
  await ElMessageBox.confirm(`确认 ${row.report_period} 监管报表？确认后将进入已确认状态。`, '确认报表', { type: 'warning' })
  await http.put('/api/government/reports/' + row.id + '/confirm'); ElMessage.success('报表已确认'); await load()
}
onMounted(load)
</script>

<style scoped>
.stats { margin-bottom: 16px; }
.content-tabs { background: #fff; padding: 0 16px 16px; }
.muted { color: #909399; font-size: 13px; }
</style>
