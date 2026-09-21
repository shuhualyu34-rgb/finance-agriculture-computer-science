<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="role" clearable placeholder="全部角色" style="width: 150px" @change="load">
        <el-option v-for="(t, k) in roleMap" :key="k" :label="t" :value="k" />
      </el-select>
      <el-input v-model="q" placeholder="姓名/手机号搜索" style="width: 220px" clearable @keyup.enter="load" @clear="load" />
      <el-button type="primary" @click="load">搜索</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" width="130" />
      <el-table-column prop="real_name" label="姓名" width="110" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column label="角色">
        <template #default="{ row }">
          <el-tag v-for="r in row.roles" :key="r" style="margin-right: 4px">{{ roleMap[r] || r }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'danger'">{{ userStatusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="150">
        <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import http from '../api'
import { fmtDateTime, roleMap, userStatusMap } from '../utils/format'

const role = ref('')
const q = ref('')
const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const params = {}
    if (role.value) params.role = role.value
    if (q.value) params.q = q.value
    rows.value = await http.get('/api/admin/users', { params })
  } finally { loading.value = false }
}

onMounted(load)
</script>
