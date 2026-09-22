import { createRouter, createWebHistory } from 'vue-router'
import { auth, hasRole } from '../store/auth'
import Layout from '../layout/AppLayout.vue'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: Layout,
    redirect: '/loans',
    children: [
      { path: 'loans', name: 'loans', component: () => import('../views/Loans.vue'), meta: { title: '授信审批', roles: ['BANK', 'ADMIN'] } },
      { path: 'government', name: 'government', component: () => import('../views/Government.vue'), meta: { title: '政府监管', roles: ['GOVERNMENT', 'ADMIN'] } },
      { path: 'policies', name: 'policies', component: () => import('../views/Policies.vue'), meta: { title: '保单管理', roles: ['INSURANCE', 'ADMIN'] } },
      { path: 'claims/new', name: 'claimNew', component: () => import('../views/ClaimCreate.vue'), meta: { title: '理赔处理', roles: ['INSURANCE', 'ADMIN'] } },
      { path: 'claims', name: 'claims', component: () => import('../views/Claims.vue'), meta: { title: '理赔台账', roles: ['INSURANCE', 'ADMIN'] } },
      { path: 'certifications', name: 'certifications', component: () => import('../views/Certifications.vue'), meta: { title: '认证审批', roles: ['OPERATOR', 'ADMIN'] } },
      { path: 'standards', name: 'standards', component: () => import('../views/Standards.vue'), meta: { title: '标准管理', roles: ['OPERATOR', 'ADMIN'] } },
      { path: 'trace-codes', name: 'traceCodes', component: () => import('../views/TraceCodes.vue'), meta: { title: '溯源码管理', roles: ['OPERATOR', 'ADMIN'] } },
      { path: 'orders', name: 'orders', component: () => import('../views/Orders.vue'), meta: { title: '订单管理', roles: ['OPERATOR', 'ADMIN'] } },
      { path: 'dividends', name: 'dividends', component: () => import('../views/Dividends.vue'), meta: { title: '分红计算', roles: ['OPERATOR', 'ADMIN'] } },
      { path: 'users', name: 'users', component: () => import('../views/Users.vue'), meta: { title: '用户管理', roles: ['ADMIN'] } },
      { path: 'plots', name: 'plots', component: () => import('../views/Plots.vue'), meta: { title: '认养管理', roles: ['ADMIN'] } },
      { path: 'config', name: 'config', component: () => import('../views/Config.vue'), meta: { title: '数据配置', roles: ['ADMIN'] } },
      { path: 'no-permission', name: 'noPermission', component: () => import('../views/NoPermission.vue'), meta: { title: '无权限' } }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!auth.token) return '/login'
  if (to.meta.roles && !hasRole(...to.meta.roles)) return '/no-permission'
  return true
})

export default router
