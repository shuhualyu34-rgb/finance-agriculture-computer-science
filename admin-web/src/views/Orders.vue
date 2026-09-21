<template>
  <div class="page">
    <el-tabs v-model="tab" @tab-change="load">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待发货" name="PAID" />
      <el-tab-pane label="已发货" name="SHIPPED" />
      <el-tab-pane label="已完成" name="COMPLETED" />
    </el-tabs>
    <el-table :data="rows" v-loading="loading" border stripe>
      <el-table-column prop="order_no" label="订单号" width="160" />
      <el-table-column prop="consumer_name" label="消费者" width="90" />
      <el-table-column prop="consumer_phone" label="电话" width="120" />
      <el-table-column prop="product_summary" label="商品摘要" min-width="160" />
      <el-table-column label="金额" width="110">
        <template #default="{ row }">{{ fmtMoney(row.total_amount) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="tagType(row.status)">{{ orderStatusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="物流" width="150">
        <template #default="{ row }">
          <span v-if="row.carrier">{{ row.carrier }} {{ row.tracking_no }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="下单时间" width="140">
        <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="收货信息" width="100">
        <template #default="{ row }">
          <el-popover v-if="addr(row)" placement="left" width="260" trigger="hover">
            <template #reference>
              <el-button link type="primary">查看</el-button>
            </template>
            <p><b>{{ addr(row).receiver }}</b> {{ addr(row).phone }}</p>
            <p>{{ addr(row).detail_address }}</p>
          </el-popover>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'PAID'" link type="primary" @click="openShip(row)">发货</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="shipVisible" title="订单发货" width="440px">
      <p>订单号：{{ current?.order_no }}，金额 {{ fmtMoney(current?.total_amount) }}</p>
      <el-form label-width="80px">
        <el-form-item label="快递公司">
          <el-input v-model="ship.carrier" placeholder="如：顺丰速运" />
        </el-form-item>
        <el-form-item label="快递单号">
          <el-input v-model="ship.tracking_no" placeholder="请输入快递单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitShip">确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { fmtDateTime, fmtMoney, orderStatusMap } from '../utils/format'

const tab = ref('')
const rows = ref([])
const loading = ref(false)
const shipVisible = ref(false)
const current = ref(null)
const ship = reactive({ carrier: '', tracking_no: '' })
const saving = ref(false)

function tagType(s) {
  return { PENDING_PAYMENT: 'info', PAID: 'warning', SHIPPED: 'primary', COMPLETED: 'success' }[s] || 'info'
}

function addr(row) {
  try {
    const a = typeof row.address_snapshot === 'string' ? JSON.parse(row.address_snapshot) : row.address_snapshot
    return a && a.receiver ? a : null
  } catch (e) { return null }
}

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/api/shop/orders', { params: tab.value ? { status: tab.value } : {} })
  } finally { loading.value = false }
}

function openShip(row) {
  current.value = row
  ship.carrier = ''
  ship.tracking_no = ''
  shipVisible.value = true
}

async function submitShip() {
  if (!ship.carrier) return ElMessage.warning('请填写快递公司')
  if (!ship.tracking_no) return ElMessage.warning('请填写快递单号')
  saving.value = true
  try {
    await http.put('/api/shop/orders/' + current.value.id + '/ship', { ...ship })
    ElMessage.success('发货成功')
    shipVisible.value = false
    load()
  } finally { saving.value = false }
}

onMounted(load)
</script>
