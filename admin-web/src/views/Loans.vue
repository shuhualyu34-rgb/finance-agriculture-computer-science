<template>
  <div class="page">
    <el-tabs v-model="tab" @tab-change="load">
      <el-tab-pane label="待审批" name="PENDING" />
      <el-tab-pane label="已通过" name="APPROVED" />
      <el-tab-pane label="已驳回" name="REJECTED" />
    </el-tabs>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="application_no" label="申请编号" width="150" />
      <el-table-column prop="farmer_name" label="农户" width="90" />
      <el-table-column prop="farmer_phone" label="手机号" width="120" />
      <el-table-column prop="plot_name" label="地块" min-width="110" />
      <el-table-column prop="area_mu" label="面积(亩)" width="90" />
      <el-table-column label="建议额度" width="110">
        <template #default="{ row }">{{ fmtMoney(row.suggested_amount) }}</template>
      </el-table-column>
      <el-table-column label="风险等级" width="90">
        <template #default="{ row }">{{ riskMap[row.risk_level] || row.risk_level }}</template>
      </el-table-column>
      <el-table-column label="认证状态" width="90">
        <template #default="{ row }">{{ certStatusMap[row.certification_status] || row.certification_status }}</template>
      </el-table-column>
      <el-table-column prop="policy_count" label="保单数" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.bank_result === 'APPROVED' ? 'success' : row.bank_result === 'REJECTED' ? 'danger' : 'warning'">
            {{ loanResultMap[row.bank_result] || row.bank_result }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="申请时间" width="140">
        <template #default="{ row }">{{ fmtDateTime(row.applied_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="showProfile(row)">画像</el-button>
          <el-button v-if="row.bank_result === 'PENDING'" link type="success" @click="openReview(row)">审批</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="profileVisible" size="600px" :title="'农户画像 - ' + (profile?.real_name || '')">
      <div v-if="profile">
        <el-descriptions :column="2" border size="small" title="基本信息">
          <el-descriptions-item label="姓名">{{ profile.real_name }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ profile.phone }}</el-descriptions-item>
          <el-descriptions-item label="村组">{{ profile.village || '-' }}</el-descriptions-item>
          <el-descriptions-item label="认证状态">{{ certStatusMap[profile.certification_status] || profile.certification_status }}</el-descriptions-item>
        </el-descriptions>

        <h4>信用评分（算法模型）</h4>
        <el-alert
          v-if="credit && credit.model_status && !credit.model_status.enabled"
          type="warning" :closable="false" show-icon
          :title="credit.note || '评分卡未启用，当前为规则评分'"
          style="margin-bottom: 8px"
        />
        <el-descriptions v-if="credit" :column="3" border size="small">
          <el-descriptions-item label="信用评分">
            <span
              :style="{
                fontSize: '20px', fontWeight: 700,
                color: credit.score >= 600 ? '#67c23a' : credit.score >= 450 ? '#e6a23c' : '#f56c6c'
              }"
            >{{ credit.score }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="credit.risk_level === 'LOW' ? 'success' : credit.risk_level === 'MEDIUM' ? 'warning' : 'danger'">
              {{ riskMap[credit.risk_level] || credit.risk_level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="违约概率">
            {{ credit.default_probability != null ? (credit.default_probability * 100).toFixed(2) + '%' : '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <h4>地块（{{ profile.plots?.length || 0 }}）</h4>
        <el-table :data="profile.plots || []" size="small" border>
          <el-table-column prop="plot_code" label="地块编码" />
          <el-table-column prop="plot_name" label="名称" />
          <el-table-column prop="area_mu" label="面积(亩)" />
          <el-table-column prop="variety" label="品种" />
        </el-table>
        <h4>保单（{{ profile.policies?.length || 0 }}）</h4>
        <el-table :data="profile.policies || []" size="small" border>
          <el-table-column prop="policy_no" label="保单号" />
          <el-table-column prop="product_name" label="产品" />
          <el-table-column label="保额">
            <template #default="{ row }">{{ fmtMoney(row.insured_amount) }}</template>
          </el-table-column>
          <el-table-column label="状态">
            <template #default="{ row }">{{ policyStatusMap[row.status] || row.status }}</template>
          </el-table-column>
        </el-table>
        <h4>最近农事记录</h4>
        <el-table :data="(profile.records || []).slice(0, 30)" size="small" border>
          <el-table-column prop="record_type" label="类型" width="90" />
          <el-table-column prop="content" label="内容" />
          <el-table-column label="时间" width="140">
            <template #default="{ row }">{{ fmtDateTime(row.performed_at || row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <el-dialog v-model="reviewVisible" title="授信审批" width="460px">
      <p>申请编号：{{ current?.application_no }}，建议额度 {{ fmtMoney(current?.suggested_amount) }}</p>
      <el-form label-width="70px">
        <el-form-item label="审批结果">
          <el-radio-group v-model="review.result">
            <el-radio label="APPROVED">通过</el-radio>
            <el-radio label="REJECTED">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="review.note" type="textarea" :rows="3" placeholder="审批备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitReview">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtDateTime, fmtMoney, loanResultMap, certStatusMap, policyStatusMap, riskMap } from '../utils/format'

const tab = ref('PENDING')
const rows = ref([])
const loading = ref(false)
const profileVisible = ref(false)
const profile = ref(null)
const credit = ref(null)
const reviewVisible = ref(false)
const current = ref(null)
const review = ref({ result: 'APPROVED', note: '' })
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/bank/loans', { params: { result: tab.value } })
  } finally { loading.value = false }
}

async function showProfile(row) {
  profile.value = null
  credit.value = null
  profileVisible.value = true
  profile.value = await http.get('/api/bank/farmers/' + row.farmer_id)
  try {
    credit.value = await http.get('/api/bank/credit-score/' + row.farmer_id)
  } catch (e) { /* 评分接口异常不影响画像展示 */ }
}

function openReview(row) {
  current.value = row
  review.value = { result: 'APPROVED', note: '' }
  reviewVisible.value = true
}

async function submitReview() {
  saving.value = true
  try {
    await http.put('/api/bank/loans/' + current.value.id + '/review', { result: review.value.result, note: review.value.note })
    ElMessage.success('审批完成')
    reviewVisible.value = false
    load()
  } finally { saving.value = false }
}

onMounted(load)
</script>
