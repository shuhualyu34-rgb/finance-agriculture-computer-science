<template>
  <div class="page">
    <div class="toolbar">
      <span>标准版本：</span>
      <el-select v-model="versionId" style="width: 320px" @change="group">
        <el-option v-for="s in standards" :key="s.id" :value="s.id" :label="'V' + s.version_no + ' - ' + s.title" />
      </el-select>
    </div>
    <el-card v-for="g in groups" :key="g.stage" style="margin-bottom: 12px">
      <template #header>
        <b>{{ stageMap[g.stage] }}</b>（{{ g.clauses.length }} 条）
      </template>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item v-for="c in g.clauses" :key="c.id" :label="c.clause_code + ' ' + c.clause_name">
          {{ c.requirement }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '../api'
import { stageMap } from '../utils/format'

const standards = ref([])
const versionId = ref(null)

const current = computed(() => standards.value.find((s) => s.id === versionId.value))
const groups = computed(() => {
  if (!current.value || !current.value.clauses) return []
  const order = ['PLANTING', 'PROCESSING', 'QUALITY', 'GRADING', 'PACKAGING', 'DISTRIBUTION']
  return order
    .map((stage) => ({ stage, clauses: current.value.clauses.filter((c) => c.stage === stage) }))
    .filter((g) => g.clauses.length > 0)
})

function group() { /* computed 处理 */ }

onMounted(async () => {
  standards.value = await http.get('/api/operator/standards')
  if (standards.value.length) versionId.value = standards.value[0].id
})
</script>
