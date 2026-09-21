<template>
  <div class="page">
    <el-card>
      <template #header>录入理赔</template>
      <el-form label-width="110px" style="max-width: 640px">
        <el-form-item label="选择保单">
          <el-select v-model="policyId" filterable placeholder="请选择保单" style="width: 100%" @change="preview">
            <el-option v-for="p in policies" :key="p.id" :value="p.id"
              :label="p.policy_no + ' - ' + p.farmer_name + ' - ' + p.plot_name" />
          </el-select>
        </el-form-item>
        <el-form-item label="受灾说明">
          <el-input v-model="form.disaster_note" type="textarea" :rows="3" placeholder="请描述受灾情况" />
        </el-form-item>
        <el-form-item label="受灾比例">
          <el-slider v-model="ratePercent" :min="0" :max="100" :step="5" show-input @input="preview" />
        </el-form-item>
        <el-form-item label="赔付预览">
          <span class="preview">{{ fmtMoney(previewAmount) }}</span>
          <span class="tip" v-if="policy">（保额 {{ fmtMoney(policy.insured_amount) }} × {{ ratePercent }}%）</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">提交理赔</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtMoney } from '../utils/format'

const route = useRoute()
const router = useRouter()
const policies = ref([])
const policyId = ref(null)
const form = reactive({ disaster_note: '' })
const ratePercent = ref(50)
const saving = ref(false)

const policy = computed(() => policies.value.find((p) => p.id === policyId.value))
const previewAmount = computed(() => (policy.value ? ((policy.value.insured_amount * ratePercent.value) / 100) : 0))

function preview() { /* computed 自动计算 */ }

async function submit() {
  if (!policyId.value) return ElMessage.warning('请选择保单')
  if (!form.disaster_note) return ElMessage.warning('请填写受灾说明')
  saving.value = true
  try {
    const res = await http.post('/api/insurance/claims', {
      policy_id: policyId.value,
      disaster_note: form.disaster_note,
      disaster_rate: ratePercent.value / 100
    })
    ElMessage.success('理赔已提交，赔付金额 ' + fmtMoney(res.claim_amount))
    router.push('/claims')
  } finally { saving.value = false }
}

onMounted(async () => {
  policies.value = await http.get('/api/insurance/policies')
  if (route.query.policy_id) policyId.value = Number(route.query.policy_id)
})
</script>

<style scoped>
.preview { font-size: 20px; font-weight: bold; color: #e6a23c; }
.tip { color: #909399; margin-left: 8px; }
</style>
