<template>
  <div class="page">
    <el-tabs v-model="tab" @tab-change="load">
      <el-tab-pane label="待审核" name="PENDING" />
      <el-tab-pane label="已通过" name="APPROVED" />
      <el-tab-pane label="已驳回" name="REJECTED" />
      <el-tab-pane label="退回整改" name="RECTIFYING" />
    </el-tabs>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="farmer_name" label="农户" width="90" />
      <el-table-column prop="farmer_phone" label="手机号" width="120" />
      <el-table-column prop="plot_name" label="地块" min-width="110" />
      <el-table-column prop="plot_code" label="地块编码" width="130" />
      <el-table-column prop="area_mu" label="面积(亩)" width="90" />
      <el-table-column prop="version_no" label="标准版本" width="100" />
      <el-table-column prop="standard_title" label="标准名称" min-width="140" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'APPROVED' ? 'success' : row.status === 'REJECTED' ? 'danger' : row.status === 'RECTIFYING' ? 'info' : 'warning'">
            {{ certStatusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="提交时间" width="140">
        <template #default="{ row }">{{ fmtDateTime(row.submitted_at) }}</template>
      </el-table-column>
      <el-table-column prop="review_note" label="审批备注" min-width="120" />
      <el-table-column v-if="tab === 'PENDING'" label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openReview(row)">审批</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="认证审批" width="460px">
      <el-form label-width="80px">
        <el-form-item label="审批结论">
          <el-radio-group v-model="form.status">
            <el-radio label="APPROVED">通过（升级为已认证农户）</el-radio>
          </el-radio-group>
          <div>
            <el-radio-group v-model="form.status">
              <el-radio label="REJECTED">驳回</el-radio>
              <el-radio label="RECTIFYING">退回整改</el-radio>
            </el-radio-group>
          </div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" placeholder="审批备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtDateTime, certStatusMap } from '../utils/format'

const tab = ref('PENDING')
const rows = ref([])
const loading = ref(false)
const visible = ref(false)
const current = ref(null)
const form = reactive({ status: 'APPROVED', note: '' })
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const all = await http.get('/api/admin/certifications')
    rows.value = tab.value ? all.filter((r) => r.status === tab.value) : all
  } finally { loading.value = false }
}

function openReview(row) {
  current.value = row
  form.status = 'APPROVED'
  form.note = ''
  visible.value = true
}

async function submit() {
  saving.value = true
  try {
    await http.put('/api/admin/certifications/' + current.value.id + '/review', { status: form.status, note: form.note })
    ElMessage.success('审批完成')
    visible.value = false
    load()
  } finally { saving.value = false }
}

onMounted(load)
</script>
