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
import type {
  DispatchBatchDetail,
  DispatchBatchSummary,
  NodeDispatchCreatePayload,
  NodeDispatchResult,
} from '@/types/dispatch'
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
let batchesData: DispatchBatchSummary[] | null = null
let batchDetailsData: Record<string, DispatchBatchDetail> | null = null

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

/** 将真实 API 返回的方案写入 Mock 缓存，供节点间调度 Mock 使用 */
export async function registerMockScheduleDetail(
  detail: GlobalScheduleDetail,
): Promise<void> {
  await ensureMockSchedules()
  scheduleDetailsData![detail.schedule_code] = detail
  const summary: GlobalScheduleSummary = {
    schedule_code: detail.schedule_code,
    total_distance: detail.total_distance,
    total_time: detail.total_time,
    total_goods: detail.total_goods,
    score: detail.score,
    package_count: detail.package_count,
    version: detail.version,
    is_replan: detail.is_replan,
    created_at: detail.created_at,
  }
  if (!schedulesData!.some((s) => s.schedule_code === detail.schedule_code)) {
    schedulesData = [summary, ...schedulesData!]
  }
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


async function ensureMockBatches(): Promise<void> {
  if (!batchesData) {
    batchesData = await loadJson<DispatchBatchSummary>('/mock/batches.json')
  }
  if (!batchDetailsData) {
    const res = await fetch('/mock/batch-details.json')
    if (!res.ok) throw new Error('加载 Mock 数据失败: /mock/batch-details.json')
    batchDetailsData = (await res.json()) as Record<string, DispatchBatchDetail>
  }
}

export async function getMockBatches(): Promise<DispatchBatchSummary[]> {
  await ensureMockBatches()
  return batchesData!
}

export async function getMockBatchDetail(
  batchCode: string,
): Promise<DispatchBatchDetail | null> {
  await ensureMockBatches()
  return batchDetailsData![batchCode] ?? null
}

function buildMockDispatchDetail(
  batchCode: string,
  scheduleCode: string,
): DispatchBatchDetail {
  const l0Phase = {
    level_phase: 0 as const,
    dispatch_code: `ND${batchCode.slice(2)}L0`,
    vehicle_tasks: [
      {
        vehicle_code: 'VEHSC00101',
        driver_code: 'DRVSC00101',
        distance: 12.5,
        tasks: [
          {
            from_node_code: 'SC001',
            to_node_code: 'L1001',
            package_codes: ['PKG001', 'PKG002'],
          },
        ],
      },
      {
        vehicle_code: 'VEHSC00201',
        driver_code: 'DRVSC00201',
        distance: 18.3,
        tasks: [
          {
            from_node_code: 'SC002',
            to_node_code: 'L1002',
            package_codes: ['PKG003'],
          },
        ],
      },
    ],
  }

  const l1Phase = {
    level_phase: 1 as const,
    dispatch_code: `ND${batchCode.slice(2)}L1`,
    vehicle_tasks: [
      {
        vehicle_code: 'VEHL100101',
        driver_code: 'DRVL100101',
        distance: 22.1,
        tasks: [
          {
            from_node_code: 'L1001',
            to_node_code: 'L2001',
            package_codes: ['PKG001', 'PKG002'],
          },
        ],
      },
      {
        vehicle_code: 'VEHL100201',
        driver_code: 'DRVL100201',
        distance: 15.8,
        tasks: [
          {
            from_node_code: 'L1002',
            to_node_code: 'L2005',
            package_codes: ['PKG003'],
          },
        ],
      },
    ],
  }

  const dispatches = [l0Phase, l1Phase]
  const vehicleCount = new Set(
    dispatches.flatMap((d) => d.vehicle_tasks.map((v) => v.vehicle_code)),
  ).size
  const now = new Date().toISOString().slice(0, 19)

  return {
    batch_code: batchCode,
    schedule_code: scheduleCode,
    status: 'completed',
    vehicle_count: vehicleCount,
    l0_l1_dispatch_count: l0Phase.vehicle_tasks.length,
    l1_l2_dispatch_count: l1Phase.vehicle_tasks.length,
    route_codes: ['RT001', 'RT002'],
    created_at: now,
    dispatches,
  }
}

export async function createMockNodeDispatch(
  payload: NodeDispatchCreatePayload,
): Promise<NodeDispatchResult> {
  await ensureMockBatches()
  await ensureMockSchedules()

  const scheduleCode = payload.schedule_code
  const detail = scheduleDetailsData![scheduleCode]
  if (!detail) {
    throw new Error('请先选择有效的全局调度方案')
  }

  if (payload.simulate_failure === 'no_packages' || (detail.package_count ?? 0) === 0) {
    throw new Error('无可用包裹，无法生成节点间调度')
  }
  if (payload.simulate_failure === 'no_vehicles') {
    throw new Error('无可用车辆，无法生成节点间调度')
  }
  if (payload.simulate_failure === 'first_phase_fail') {
    throw new Error('L0→L1 调度失败，未执行 L1→L2')
  }

  await delay(1500)

  const batchCode = nextCode(
    'DB',
    batchesData!.map((b) => b.batch_code),
  )
  const batchDetail = buildMockDispatchDetail(batchCode, scheduleCode)

  const summary: DispatchBatchSummary = {
    batch_code: batchDetail.batch_code,
    schedule_code: batchDetail.schedule_code,
    status: batchDetail.status,
    vehicle_count: batchDetail.vehicle_count,
    l0_l1_dispatch_count: batchDetail.l0_l1_dispatch_count,
    l1_l2_dispatch_count: batchDetail.l1_l2_dispatch_count,
    created_at: batchDetail.created_at,
  }

  batchesData = [summary, ...batchesData!]
  batchDetailsData![batchCode] = batchDetail

  return {
    batch_code: batchDetail.batch_code,
    status: batchDetail.status,
    l0_l1_dispatch_count: batchDetail.l0_l1_dispatch_count!,
    l1_l2_dispatch_count: batchDetail.l1_l2_dispatch_count!,
    route_codes: batchDetail.route_codes,
  }
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
