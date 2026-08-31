import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { ROUTE_PERMISSIONS } from '@/constants/permissions'
import type { NodeType } from '@/types/node'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    nodeType?: NodeType
    title?: string
    permission?: string
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
          meta: { permission: 'schedule:read' },
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('@/views/orders/OrderList.vue'),
          meta: { title: '订单管理', permission: 'orders:read' },
        },
        {
          path: 'goods',
          name: 'Goods',
          component: () => import('@/views/goods/GoodsList.vue'),
          meta: { title: '货物管理', permission: 'goods:read' },
        },
        {
          path: 'packages',
          name: 'Packages',
          component: () => import('@/views/packages/PackageList.vue'),
          meta: { title: '包裹管理', permission: 'packages:read' },
        },
        {
          path: 'vehicles',
          name: 'Vehicles',
          component: () => import('@/views/vehicles/VehicleList.vue'),
          meta: { title: '车辆管理', permission: 'vehicles:read' },
        },
        {
          path: 'drivers',
          name: 'Drivers',
          component: () => import('@/views/drivers/DriverList.vue'),
          meta: { title: '司机管理', permission: 'drivers:read' },
        },
        {
          path: 'nodes/storage',
          name: 'StorageCenters',
          component: () => import('@/views/nodes/NodeList.vue'),
          meta: { nodeType: 'storage_center', title: '存储中心', permission: 'nodes:read' },
        },
        {
          path: 'nodes/sorting',
          name: 'SortingCenters',
          component: () => import('@/views/nodes/NodeList.vue'),
          meta: { nodeType: 'sorting_center', title: '分拣中心', permission: 'nodes:read' },
        },
        {
          path: 'exceptions',
          name: 'Exceptions',
          component: () => import('@/views/exceptions/ExceptionList.vue'),
          meta: { title: '异常管理', permission: 'exceptions:read' },
        },
        {
          path: 'arrival-confirm',
          name: 'ArrivalConfirm',
          component: () => import('@/views/arrival/ArrivalConfirm.vue'),
          meta: { title: '节点到货确认', permission: 'arrivals:confirm' },
        },
        {
          path: 'notifications',
          name: 'Notifications',
          component: () => import('@/views/settings/NotificationSettings.vue'),
          meta: { title: '消息通知', permission: 'notifications:read' },
        },
        {
          path: 'reports',
          name: 'Reports',
          component: () => import('@/views/reports/Dashboard.vue'),
          meta: { title: '报表分析', permission: 'reports:read' },
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
    return authStore.firstAllowedPath()
  }

  const requiredPermission = to.meta.permission ?? ROUTE_PERMISSIONS[to.path]
  if (requiredPermission && !authStore.can(requiredPermission)) {
    return authStore.firstAllowedPath()
  }

  return true
})

export default router