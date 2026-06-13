import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/health',
      children: [
        {
          path: 'health',
          name: 'HealthCheck',
          component: () => import('@/views/HealthCheck.vue'),
        },
      ],
    },
  ],
})

export default router
