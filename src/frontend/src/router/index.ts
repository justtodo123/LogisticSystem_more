import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { useAuthStore } from '@/stores/auth'

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
          path: 'health',
          name: 'HealthCheck',
          component: () => import('@/views/HealthCheck.vue'),
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
