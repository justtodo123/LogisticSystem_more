import type { Driver } from '@/types/driver'
import type { Goods } from '@/types/goods'
import type { NodeItem } from '@/types/node'
import type { PackageItem } from '@/types/package'
import type { Order } from '@/types/order'
import type {
  GlobalScheduleDetail,
  GlobalScheduleSummary,
} from '@/types/schedule'
import type { Vehicle } from '@/types/vehicle'
import { useMockScheduleFail } from '@/utils/env'
import { nextCode } from '@/utils/mock'

let nodesData: NodeItem[] | null = null
let ordersData: Order[] | null = null
let vehiclesData: Vehicle[] | null = null
let goodsData: Goods[] | null = null
let packagesData: PackageItem[] | null = null
let driversData: Driver[] | null = null
let schedulesData: GlobalScheduleSummary[] | null = null
let scheduleDetailsData: Record<string, GlobalScheduleDetail> | null = null

async function loadJson<T>(path: string): Promise<T[]> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`加载 Mock 数据失败: ${path}`)
  return res.json() as Promise<T[]>
}

export async function getMockNodes(): Promise<NodeItem[]> {
  if (!nodesData) {
    nodesData = await loadJson<NodeItem>('/mock/nodes.json')
  }
  return nodesData
}

export async function getMockOrders(): Promise<Order[]> {
  if (!ordersData) {
    ordersData = await loadJson<Order>('/mock/orders.json')
  }
  return ordersData
}

export async function getMockVehicles(): Promise<Vehicle[]> {
  if (!vehiclesData) {
    vehiclesData = await loadJson<Vehicle>('/mock/vehicles.json')
  }
  return vehiclesData
}

export async function getMockGoods(): Promise<Goods[]> {
  if (!goodsData) {
    goodsData = await loadJson<Goods>('/mock/goods.json')
  }
  return goodsData
}

export async function getMockPackages(): Promise<PackageItem[]> {
  if (!packagesData) {
    packagesData = await loadJson<PackageItem>('/mock/packages.json')
  }
  return packagesData
}

export async function getMockDrivers(): Promise<Driver[]> {
  if (!driversData) {
    driversData = await loadJson<Driver>('/mock/drivers.json')
  }
  return driversData
}

async function ensureMockSchedules(): Promise<void> {
  if (!schedulesData) {
    schedulesData = await loadJson<GlobalScheduleSummary>('/mock/schedules.json')
  }
  if (!scheduleDetailsData) {
    const res = await fetch('/mock/schedule-details.json')
    if (!res.ok) throw new Error('加载 Mock 数据失败: /mock/schedule-details.json')
    scheduleDetailsData = (await res.json()) as Record<string, GlobalScheduleDetail>
  }
}

export async function getMockSchedules(): Promise<GlobalScheduleSummary[]> {
  await ensureMockSchedules()
  return schedulesData!
}

export async function getMockScheduleDetail(
  scheduleCode: string,
): Promise<GlobalScheduleDetail | null> {
  await ensureMockSchedules()
  return scheduleDetailsData![scheduleCode] ?? null
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function createMockGlobalSchedule(): Promise<GlobalScheduleSummary> {
  await ensureMockSchedules()
  if (useMockScheduleFail()) {
    throw new Error('无法完成全局调度，请增加1级分拣中心容量或减少订单')
  }

  await delay(1200)

  const code = nextCode(
    'GS',
    schedulesData!.map((s) => s.schedule_code),
  )
  const now = new Date().toISOString().slice(0, 19)

  const summary: GlobalScheduleSummary = {
    schedule_code: code,
    total_distance: 102.4,
    total_time: 195,
    total_goods: 6,
    score: 82.1,
    package_count: 4,
    version: 1,
    is_replan: false,
    created_at: now,
  }

  const detail: GlobalScheduleDetail = {
    ...summary,
    algorithm_type: 'traditional',
    order_codes: ['O004'],
    goods_schedules: [
      {
        goods_code: 'GO004_1',
        order_code: 'O004',
        path: ['SC004', 'L1001', 'L2020'],
      },
      {
        goods_code: 'GO004_2',
        order_code: 'O004',
        path: ['SC004', 'L1002', 'L2021'],
      },
    ],
  }

  schedulesData = [summary, ...schedulesData!]
  scheduleDetailsData![code] = detail
  return summary
}

export function resetMockStore(): void {
  nodesData = null
  ordersData = null
  vehiclesData = null
  goodsData = null
  packagesData = null
  driversData = null
  schedulesData = null
  scheduleDetailsData = null
}
