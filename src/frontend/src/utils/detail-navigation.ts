import type { Router } from 'vue-router'

export function goToDashboardSchedule(router: Router, scheduleCode: string): void {
  void router.push({ path: '/dashboard', query: { schedule: scheduleCode } })
}

export function goToPackages(
  router: Router,
  query?: { status?: string; package_code?: string },
): void {
  void router.push({ path: '/packages', query: query ?? {} })
}

export function goToOrders(router: Router, orderCode?: string): void {
  void router.push({
    path: '/orders',
    query: orderCode ? { order_code: orderCode } : {},
  })
}
