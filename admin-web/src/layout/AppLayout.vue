<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #1f2d3d">
      <div class="logo">丹邱丝苗米<br/>普惠产融服务平台</div>
      <el-menu :default-active="$route.path" router background-color="#1f2d3d" text-color="#cfd8e3" active-text-color="#409EFF">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">管理后台 · {{ $route.meta.title || '' }}</div>
        <div class="header-right">
          <span class="user">{{ auth.user?.real_name }}（{{ roleText }}）</span>
          <el-button size="small" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { auth, clearAuth, hasRole } from '../store/auth'
import { roleMap } from '../utils/format'

const router = useRouter()

const allMenus = [
  { path: '/loans', title: '授信审批', roles: ['BANK', 'ADMIN'] },
  { path: '/policies', title: '保单管理', roles: ['INSURANCE', 'ADMIN'] },
  { path: '/claims/new', title: '理赔处理', roles: ['INSURANCE', 'ADMIN'] },
  { path: '/claims', title: '理赔台账', roles: ['INSURANCE', 'ADMIN'] },
  { path: '/certifications', title: '认证审批', roles: ['OPERATOR', 'ADMIN'] },
  { path: '/standards', title: '标准管理', roles: ['OPERATOR', 'ADMIN'] },
  { path: '/trace-codes', title: '溯源码管理', roles: ['OPERATOR', 'ADMIN'] },
  { path: '/orders', title: '订单管理', roles: ['OPERATOR', 'ADMIN'] },
  { path: '/dividends', title: '分红计算', roles: ['OPERATOR', 'ADMIN'] },
  { path: '/users', title: '用户管理', roles: ['ADMIN'] },
  { path: '/plots', title: '认养管理', roles: ['ADMIN'] },
  { path: '/config', title: '数据配置', roles: ['ADMIN'] }
]

const menus = computed(() => allMenus.filter((m) => hasRole(...m.roles)))
const roleText = computed(() => (auth.user?.roles || []).map((r) => roleMap[r] || r).join('、'))

function logout() {
  clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.logo { color: #fff; font-size: 15px; font-weight: bold; padding: 18px 16px; line-height: 1.6; }
.header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e6e8eb; }
.header-title { font-size: 16px; font-weight: 600; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user { color: #606266; }
</style>
