import { createRouter, createWebHistory } from 'vue-router'
import { getAuth } from './api'

import Entry from './views/Entry.vue'
import Login from './views/Login.vue'
import FarmerLayout from './views/farmer/Layout.vue'
import FarmerHome from './views/farmer/Home.vue'
import FarmerPlots from './views/farmer/Plots.vue'
import FarmerPlotDetail from './views/farmer/PlotDetail.vue'
import FarmerUpload from './views/farmer/Upload.vue'
import FarmerApply from './views/farmer/Apply.vue'
import FarmerMine from './views/farmer/Mine.vue'
import FarmerIncome from './views/farmer/Income.vue'
import ConsumerTrace from './views/consumer/Trace.vue'
import ConsumerAdopt from './views/consumer/Adopt.vue'
import ConsumerMine from './views/consumer/Mine.vue'
import ConsumerShop from './views/consumer/Shop.vue'
import ConsumerOrders from './views/consumer/Orders.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Entry },
    {
      path: '/farmer/login',
      component: Login,
      props: { side: 'farmer' },
    },
    {
      path: '/farmer',
      component: FarmerLayout,
      children: [
        { path: '', name: 'farmer-home', component: FarmerHome, meta: { role: 'FARMER', tab: 'home' } },
        { path: 'plots', name: 'farmer-plots', component: FarmerPlots, meta: { role: 'FARMER', tab: 'plots' } },
        { path: 'upload', name: 'farmer-upload', component: FarmerUpload, meta: { role: 'FARMER', tab: 'upload' } },
        { path: 'mine', name: 'farmer-mine', component: FarmerMine, meta: { role: 'FARMER', tab: 'mine' } },
      ],
    },
    {
      path: '/farmer/plots/:id',
      component: FarmerPlotDetail,
      meta: { role: 'FARMER' },
    },
    {
      path: '/farmer/apply',
      component: FarmerApply,
      meta: { role: 'FARMER' },
    },
    {
      path: '/farmer/income',
      component: FarmerIncome,
      meta: { role: 'FARMER' },
    },
    {
      path: '/consumer/login',
      component: Login,
      props: { side: 'consumer' },
    },
    { path: '/consumer', component: ConsumerTrace },
    { path: '/consumer/adopt', component: ConsumerAdopt, meta: { role: 'CONSUMER' } },
    { path: '/consumer/mine', component: ConsumerMine, meta: { role: 'CONSUMER' } },
    { path: '/consumer/shop', component: ConsumerShop },
    { path: '/consumer/orders', component: ConsumerOrders, meta: { role: 'CONSUMER' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.role) return true
  const auth = getAuth()
  if (!auth || !auth.token) {
    const login = to.path.startsWith('/farmer') ? '/farmer/login' : '/consumer/login'
    return { path: login, query: { redirect: to.fullPath } }
  }
  const roles = (auth.user && auth.user.roles) || []
  if (!roles.includes(to.meta.role)) {
    const login = to.path.startsWith('/farmer') ? '/farmer/login' : '/consumer/login'
    return { path: login, query: { redirect: to.fullPath, err: 'role' } }
  }
  return true
})

export default router
