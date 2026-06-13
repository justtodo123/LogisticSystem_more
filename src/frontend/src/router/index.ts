import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type { NodeType } from '@/types/node'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    nodeType?: NodeType
    title?: string
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('@/views/orders/OrderList.vue'),
          meta: { title: '订单管理' },
        },
        {
          path: 'goods',
          name: 'Goods',
          component: () => import('@/views/goods/GoodsList.vue'),
          meta: { title: '货物管理' },
        },
        {
          path: 'packages',
          name: 'Packages',
          component: () => import('@/views/packages/PackageList.vue'),
          meta: { title: '包裹管理' },
        },
        {
          path: 'vehicles',
          name: 'Vehicles',
          component: () => import('@/views/vehicles/VehicleList.vue'),
          meta: { title: '车辆管理' },
        },
        {
          path: 'drivers',
          name: 'Drivers',
          component: () => import('@/views/drivers/DriverList.vue'),
          meta: { title: '司机管理' },
        },
        {
          path: 'nodes/storage',
          name: 'StorageCenters',
          component: () => import('@/views/nodes/NodeList.vue'),
          meta: { nodeType: 'storage_center', title: '存储中心' },
        },
        {
          path: 'nodes/sorting',
          name: 'SortingCenters',
          component: () => import('@/views/nodes/NodeList.vue'),
          meta: { nodeType: 'sorting_center', title: '分拣中心' },
        },
        {
          path: 'health',
          name: 'HealthCheck',
          component: () => import('@/views/HealthCheck.vue'),
          meta: { title: '联通测试' },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.isReady) {
    await authStore.restore()
  }

  const isPublic = to.meta.public === true

  if (!authStore.isLoggedIn && !isPublic) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (authStore.isLoggedIn && to.path === '/login') {
    return '/dashboard'
  }

  return true
})

export default router