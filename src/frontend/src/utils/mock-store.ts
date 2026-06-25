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
  NodeDispatchPhase,
  NodeDispatchResult,
} from '@/types/dispatch'
import { useMockScheduleFail } from '@/utils/env'
import { normalizeBatchDetail } from '@/utils/dispatch-normalize'
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

export async function updateMockBatchDetail(
  detail: DispatchBatchDetail,
): Promise<void> {
  await ensureMockBatches()
  batchDetailsData![detail.batch_code] = detail
}

export async function updateMockBatchSummary(
  detail: DispatchBatchDetail,
): Promise<void> {
  await ensureMockBatches()
  const idx = batchesData!.findIndex((b) => b.batch_code === detail.batch_code)
  const summary: DispatchBatchSummary = {
    batch_code: detail.batch_code,
    schedule_code: detail.schedule_code,
    status: detail.status,
    vehicle_count: detail.vehicle_count,
    l0_l1_dispatch_count: detail.l0_l1_dispatch_count,
    l1_l2_dispatch_count: detail.l1_l2_dispatch_count,
    demo_mode: detail.demo_mode,
    created_at: detail.created_at,
  }
  if (idx >= 0) {
    batchesData![idx] = summary
  }
}

function buildL0Phase(batchCode: string): NodeDispatchPhase {
  return {
    level_phase: 0,
    dispatch_code: `ND${batchCode.slice(2)}L0`,
    vehicle_tasks: [
      {
        vehicle_code: '鄂A12345',
        driver_code: 'D20260601001',
        distance: 12.5,
        tasks: [
          {
            from_node_code: 'SC001',
            to_node_code: 'L1001',
            package_codes: ['PKG20260612001'],
            is_return: false,
          },
          {
            from_node_code: 'L1001',
            to_node_code: 'SC001',
            package_codes: [],
            is_return: true,
          },
        ],
      },
      {
        vehicle_code: '鄂A12346',
        driver_code: 'D20260601002',
        distance: 18.3,
        tasks: [
          {
            from_node_code: 'SC002',
            to_node_code: 'L1002',
            package_codes: ['PKG20260612002'],
            is_return: false,
          },
          {
            from_node_code: 'L1002',
            to_node_code: 'SC002',
            package_codes: [],
            is_return: true,
          },
        ],
      },
    ],
  }
}

function buildL1Phase(batchCode: string): NodeDispatchPhase {
  return {
    level_phase: 1,
    dispatch_code: `ND${batchCode.slice(2)}L1`,
    vehicle_tasks: [
      {
        vehicle_code: '鄂A12347',
        driver_code: 'D20260601003',
        distance: 22.1,
        tasks: [
          {
            from_node_code: 'L1001',
            to_node_code: 'L2001',
            package_codes: ['PKG20260612001'],
            is_return: false,
          },
          {
            from_node_code: 'L2001',
            to_node_code: 'L1001',
            package_codes: [],
            is_return: true,
          },
        ],
      },
      {
        vehicle_code: '鄂A12348',
        driver_code: 'D20260601004',
        distance: 15.8,
        tasks: [
          {
            from_node_code: 'L1002',
            to_node_code: 'L2005',
            package_codes: ['PKG20260612002'],
            is_return: false,
          },
          {
            from_node_code: 'L2005',
            to_node_code: 'L1002',
            package_codes: [],
            is_return: true,
          },
        ],
      },
    ],
  }
}

function buildMockDispatchDetail(
  batchCode: string,
  scheduleCode: string,
  options: { demoMode: boolean; includeL1: boolean },
): DispatchBatchDetail {
  const l0Phase = buildL0Phase(batchCode)
  const phases: NodeDispatchPhase[] = [l0Phase]
  if (options.includeL1) {
    phases.push(buildL1Phase(batchCode))
  }

  const dispatches = phases
  const vehicleCount = new Set(
    dispatches.flatMap((d) => d.vehicle_tasks.map((v) => v.vehicle_code)),
  ).size
  const now = new Date().toISOString().slice(0, 19)
  const l0Count = l0Phase.vehicle_tasks.length
  const l1Count = options.includeL1 ? buildL1Phase(batchCode).vehicle_tasks.length : 0

  let status: DispatchBatchDetail['status'] = 'pending'
  if (options.demoMode && options.includeL1) {
    status = 'completed'
  } else if (!options.demoMode && options.includeL1) {
    status = 'l0_l1_done'
  }

  return normalizeBatchDetail({
    batch_code: batchCode,
    schedule_code: scheduleCode,
    status,
    demo_mode: options.demoMode,
    vehicle_count: vehicleCount,
    l0_l1_dispatch_count: l0Count,
    l1_l2_dispatch_count: l1Count,
    route_codes: options.includeL1 ? ['RT001', 'RT002'] : [],
    created_at: now,
    dispatches,
  })
}

async function markPackagesInTransit(
  packageCodes: string[],
  vehicleCodes: string[],
  driverCodes: string[],
): Promise<void> {
  const packages = await getMockPackages()
  const goods = await getMockGoods()
  const vehicles = await getMockVehicles()
  const drivers = await getMockDrivers()

  for (const code of packageCodes) {
    const pkg = packages.find((p) => p.package_code === code)
    if (!pkg) continue
    pkg.status = 'in_transit'
    for (const item of pkg.goods_items) {
      const g = goods.find((x) => x.goods_code === item.goods_code)
      if (g) g.status = 'in_transit'
    }
  }

  for (const v of vehicles) {
    if (vehicleCodes.includes(v.vehicle_code)) {
      v.status = 'delivering'
    }
  }
  for (const d of drivers) {
    if (driverCodes.includes(d.driver_code)) {
      d.status = 'busy'
    }
  }
}

function cargoPackageCodesFromDetail(detail: DispatchBatchDetail): string[] {
  const codes = new Set<string>()
  for (const d of detail.dispatches) {
    for (const task of d.tasks) {
      if (task.is_return) continue
      for (const pkg of task.package_codes) {
        codes.add(pkg)
      }
    }
  }
  return [...codes]
}

function vehicleAndDriverCodes(
  detail: DispatchBatchDetail,
  levelPhase: 0 | 1,
): { vehicles: string[]; drivers: string[] } {
  const vehicles: string[] = []
  const drivers: string[] = []
  for (const d of detail.dispatches) {
    if (d.level_phase !== levelPhase) continue
    vehicles.push(d.vehicle_code)
    if (d.driver_code) drivers.push(d.driver_code)
  }
  return { vehicles, drivers }
}

async function prepareL0DispatchTransit(detail: DispatchBatchDetail): Promise<void> {
  const codes = collectPhasePackageCodes(detail, 0)
  const { vehicles, drivers } = vehicleAndDriverCodes(detail, 0)
  await markPackagesInTransit(codes, vehicles, drivers)
}

async function repackAndMarkL1Transit(detail: DispatchBatchDetail): Promise<void> {
  const packages = await getMockPackages()
  const goods = await getMockGoods()
  const codes = collectPhasePackageCodes(detail, 1)

  for (const code of codes) {
    const pkg = packages.find((p) => p.package_code === code)
    if (!pkg) continue
    pkg.status = 'in_transit'
    for (const item of pkg.goods_items) {
      const g = goods.find((x) => x.goods_code === item.goods_code)
      if (g) g.status = 'in_transit'
    }
  }

  const { vehicles, drivers } = vehicleAndDriverCodes(detail, 1)
  await markPackagesInTransit(codes, vehicles, drivers)
}

function collectPhasePackageCodes(
  detail: DispatchBatchDetail,
  levelPhase: 0 | 1,
): string[] {
  const codes = new Set<string>()
  for (const d of detail.dispatches) {
    if (d.level_phase !== levelPhase) continue
    for (const task of d.tasks) {
      if (task.is_return) continue
      for (const pkg of task.package_codes) {
        codes.add(pkg)
      }
    }
  }
  return [...codes]
}

function appendL1ToBatch(existing: DispatchBatchDetail): DispatchBatchDetail {
  const l1Phase = buildL1Phase(existing.batch_code)
  const flatL1 = normalizeBatchDetail({
    ...existing,
    dispatches: [l1Phase],
  }).dispatches

  return normalizeBatchDetail({
    ...existing,
    status: 'l0_l1_done',
    l1_l2_dispatch_count: l1Phase.vehicle_tasks.length,
    vehicle_count: new Set([
      ...existing.dispatches.map((d) => d.vehicle_code),
      ...flatL1.map((d) => d.vehicle_code),
    ]).size,
    dispatches: [...existing.dispatches, ...flatL1],
  })
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

  const demoMode = payload.demo_mode ?? false
  const scheduleBatches = batchesData!.filter((b) => b.schedule_code === scheduleCode)
  const pendingBatch = scheduleBatches.find((b) => b.status === 'l0_l1_done')

  if (!demoMode && pendingBatch) {
    const existing = batchDetailsData![pendingBatch.batch_code]
    if (!existing) {
      throw new Error('批次详情不存在')
    }
    const updated = appendL1ToBatch(existing)
    await repackAndMarkL1Transit(updated)
    batchDetailsData![updated.batch_code] = updated
    await updateMockBatchSummary(updated)
    return {
      batch_code: updated.batch_code,
      status: updated.status,
      l0_l1_dispatch_count: updated.l0_l1_dispatch_count!,
      l1_l2_dispatch_count: updated.l1_l2_dispatch_count!,
      route_codes: updated.route_codes,
    }
  }

  const batchCode = nextCode(
    'DB',
    batchesData!.map((b) => b.batch_code),
  )
  const batchDetail = buildMockDispatchDetail(batchCode, scheduleCode, {
    demoMode,
    includeL1: demoMode,
  })

  if (!demoMode) {
    await prepareL0DispatchTransit(batchDetail)
  } else {
    const codes = cargoPackageCodesFromDetail(batchDetail)
    const vehicles = batchDetail.dispatches.map((d) => d.vehicle_code)
    const drivers = batchDetail.dispatches
      .map((d) => d.driver_code)
      .filter((c): c is string => Boolean(c))
    await markPackagesInTransit(codes, vehicles, drivers)
    for (const pkg of await getMockPackages()) {
      if (codes.includes(pkg.package_code)) {
        pkg.status = 'delivered'
      }
    }
  }

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
  batchesData = null
  batchDetailsData = null
}
