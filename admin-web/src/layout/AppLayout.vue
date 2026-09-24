<template>
  <el-container class="admin-shell" :class="{ 'sidebar-open': sidebarOpen }">
    <div class="sidebar-hover-zone" role="button" tabindex="0" aria-label="展开导航菜单"
      :aria-expanded="sidebarOpen" @mouseenter="openSidebar" @focus="openSidebar"
      @keydown.enter.prevent="openSidebar" @keydown.space.prevent="openSidebar" @click="openSidebar"></div>
    <el-aside width="232px" class="admin-aside" @mouseenter="openSidebar" @mouseleave="closeSidebar">
      <div class="logo">丹邱丝苗米<br/>普惠产融服务平台
        <button class="sidebar-close" aria-label="收起导航菜单" @click.stop="closeSidebar">×</button>
      </div>
      <el-menu class="admin-menu" :default-active="$route.path" router @click="closeSidebar">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title"><span class="header-mark">🌾</span> 管理后台 <span class="header-divider">/</span> {{ $route.meta.title || '' }}</div>
        <div class="header-right">
          <span class="user">{{ auth.user?.real_name }}（{{ roleText }}）</span>
          <el-button size="small" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="admin-main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth, clearAuth, hasRole } from '../store/auth'
import { roleMap } from '../utils/format'

const router = useRouter()
const sidebarOpen = ref(false)
const openSidebar = () => { sidebarOpen.value = true }
const closeSidebar = () => { sidebarOpen.value = false }

const allMenus = [
  { path: '/loans', title: '授信审批', roles: ['BANK', 'ADMIN'] },
  { path: '/government', title: '政府监管', roles: ['GOVERNMENT', 'ADMIN'] },
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
  { path: '/config', title: '数据配置', roles: ['ADMIN'] },
  { path: '/reports', title: '监管报表', roles: ['GOVERNMENT', 'ADMIN'] },
  { path: '/inspections', title: '实地采集', roles: ['GOVERNMENT', 'ADMIN'] }
]

const menus = computed(() => allMenus.filter((m) => hasRole(...m.roles)))
const roleText = computed(() => (auth.user?.roles || []).map((r) => roleMap[r] || r).join('、'))

function logout() {
  clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.admin-shell { height: 100vh; }
.sidebar-hover-zone { position: fixed; z-index: 10; left: 0; top: 0; bottom: 0; width: 16px; cursor: pointer; }
.admin-aside { position: fixed; inset: 0 auto 0 0; height: 100vh; background: linear-gradient(180deg, #425f36, #314b31); box-shadow: 5px 0 20px rgba(46, 63, 38, .1); z-index: 11; transform: translateX(-100%); transition: transform .24s ease; }
.admin-shell.sidebar-open .admin-aside { transform: translateX(0); }
.logo { position: relative; color: #fffdf0; font-size: 16px; font-weight: 700; padding: 24px 42px 22px 20px; line-height: 1.7; letter-spacing: 1px; border-bottom: 1px solid rgba(255,255,255,.14); }
.sidebar-close { position: absolute; right: 10px; top: 12px; border: 0; padding: 2px 6px; color: #f7f5e9; background: transparent; font-size: 22px; line-height: 1; cursor: pointer; }
.logo::before { content: '🌾'; display: inline-block; margin-right: 8px; }
.admin-menu { border-right: 0; background: transparent; padding: 12px 10px; }
.admin-menu :deep(.el-menu-item) { margin: 3px 0; height: 44px; line-height: 44px; border-radius: 10px; color: #e0e8d4; }
.admin-menu :deep(.el-menu-item:hover) { color: #fff; background: rgba(255,255,255,.11); }
.admin-menu :deep(.el-menu-item.is-active) { color: #354d2d; background: #f0f1dc; font-weight: 700; }
.header { display: flex; align-items: center; justify-content: space-between; background: #fffef8; border-bottom: 1px solid #e0e1cc; box-shadow: 0 3px 14px rgba(60,75,45,.06); }
.header-title { font-size: 16px; font-weight: 700; color: #344532; }
.header-mark { margin-right: 4px; }
.header-divider { color: #b2b89c; margin: 0 8px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user { color: #66725c; }
.admin-main {
  overflow: auto;
  background: linear-gradient(180deg, rgba(255,252,236,.43), rgba(244,239,211,.36)), url('/images/rice-field-bg.jpg') center / cover fixed no-repeat;
  padding: 22px 24px;
}
@media (max-width: 760px) {
  .admin-aside { width: 232px !important; }
  .admin-main { padding: 14px; }
  .header { padding: 0 12px; }
  .header-title { font-size: 14px; }
}
@media (hover: none) {
  .sidebar-hover-zone { width: 28px; background: linear-gradient(90deg, rgba(66,95,54,.2), transparent); }
}
</style>
