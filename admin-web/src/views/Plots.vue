<template>
  <div class="page">
    <div class="toolbar">
      <el-radio-group v-model="adoptable" @change="load">
        <el-radio-button :value="''">全部</el-radio-button>
        <el-radio-button :value="'1'">开放认养</el-radio-button>
        <el-radio-button :value="'0'">未开放</el-radio-button>
      </el-radio-group>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="plot_code" label="地块编码" width="140" />
      <el-table-column prop="plot_name" label="地块名称" min-width="130" />
      <el-table-column prop="village" label="村组" min-width="110" />
      <el-table-column prop="area_mu" label="面积(亩)" width="90" />
      <el-table-column prop="variety" label="品种" min-width="110" />
      <el-table-column prop="adopted_count" label="已认养数" width="90" />
      <el-table-column label="开放认养" width="110">
        <template #default="{ row }">
          <el-switch :model-value="row.open_for_adoption" @change="(v) => toggle(row, v)" />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const adoptable = ref('')
const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const params = {}
    if (adoptable.value !== '') params.adoptable = adoptable.value
    rows.value = await http.get('/api/admin/plots', { params })
  } finally { loading.value = false }
}

async function toggle(row, v) {
  await http.put('/api/admin/plots/' + row.id + '/adoption', { open: v })
  row.open_for_adoption = v
  ElMessage.success(v ? '已开放认养' : '已关闭认养')
}

onMounted(load)
</script>
