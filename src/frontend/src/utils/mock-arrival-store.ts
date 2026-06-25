import type { NodeDispatchPhase } from '@/types/dispatch'
import type { PackageItem } from '@/types/package'
import type {
  ArrivalPackageItem,
  ConfirmArrivalPayload,
  ConfirmArrivalResult,
  GetArrivalPackagesParams,
  GetArrivalPackagesResult,
} from '@/types/simulation'
import {
  ARRIVAL_DEMO_NODE,
  ARRIVAL_DEMO_SCHEDULE,
} from '@/constants/arrival'
import { normalizeBatchDetail } from '@/utils/dispatch-normalize'
import {
  getMockGoods,
  getMockNodes,
  getMockOrders,
  getMockPackages,
  getMockScheduleDetail,
  registerMockBatch,
  registerMockScheduleDetail,
} from '@/utils/mock-store'

/** C/D/E/F 演示包裹（对齐 schedule-details GS20260613001） */
export const ARRIVAL_DEMO_PACKAGES = {
  C: 'PKG20260613001',
  D: 'PKG20260613002',
  E: 'PKG20260613003',
  F: 'PKG20260613004',
  g1: 'G20260612001',
  g2: 'G20260612002',
  order: 'O20260612001',
} as const

export const ARRIVAL_DEMO_BATCH = 'DB20260613001'

const schedulePackageRegistry = new Map<string, Set<string>>()

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function registerSchedulePackages(scheduleCode: string, codes: string[]): void {
  schedulePackageRegistry.set(scheduleCode, new Set(codes))
}

function packageBelongsToSchedule(
  scheduleCode: string,
  packageCode: string,
): boolean {
  const set = schedulePackageRegistry.get(scheduleCode)
  if (!set) return false
  return set.has(packageCode)
}

async function upsertPackage(item: PackageItem): Promise<void> {
  const packages = await getMockPackages()
  const idx = packages.findIndex((p) => p.package_code === item.package_code)
  if (idx >= 0) {
    packages[idx] = { ...packages[idx], ...item }
  } else {
    packages.push(item)
  }
}

async function syncScheduleDetailPackages(
  scheduleCode: string,
): Promise<void> {
  const detail = await getMockScheduleDetail(scheduleCode)
  if (!detail?.packages) return
  const packages = await getMockPackages()
  for (const sp of detail.packages) {
    const live = packages.find((p) => p.package_code === sp.package_code)
    if (live) {
      sp.status = live.status
    }
  }
  await registerMockScheduleDetail({ ...detail, status: 'active' })
}

function buildArrivalDemoL0Phase(batchCode: string): NodeDispatchPhase {
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
            to_node_code: ARRIVAL_DEMO_NODE,
            package_codes: [ARRIVAL_DEMO_PACKAGES.C, ARRIVAL_DEMO_PACKAGES.D],
            is_return: false,
          },
          {
            from_node_code: ARRIVAL_DEMO_NODE,
            to_node_code: 'SC001',
            package_codes: [],
            is_return: true,
          },
        ],
      },
    ],
  }
}

export function buildArrivalDemoL1Phase(batchCode: string): NodeDispatchPhase {
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
            from_node_code: ARRIVAL_DEMO_NODE,
            to_node_code: 'SO001',
            package_codes: [ARRIVAL_DEMO_PACKAGES.E],
            is_return: false,
          },
          {
            from_node_code: 'SO001',
            to_node_code: ARRIVAL_DEMO_NODE,
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
            from_node_code: ARRIVAL_DEMO_NODE,
            to_node_code: 'SO001',
            package_codes: [ARRIVAL_DEMO_PACKAGES.F],
            is_return: false,
          },
          {
            from_node_code: 'SO001',
            to_node_code: ARRIVAL_DEMO_NODE,
            package_codes: [],
            is_return: true,
          },
        ],
      },
    ],
  }
}

async function registerArrivalDemoBatch(): Promise<void> {
  const l0 = buildArrivalDemoL0Phase(ARRIVAL_DEMO_BATCH)
  const now = new Date().toISOString().slice(0, 19)
  const detail = normalizeBatchDetail({
    batch_code: ARRIVAL_DEMO_BATCH,
    schedule_code: ARRIVAL_DEMO_SCHEDULE,
    status: 'l0_l1_done',
    demo_mode: false,
    vehicle_count: 1,
    l0_l1_dispatch_count: l0.vehicle_tasks.length,
    l1_l2_dispatch_count: 0,
    route_codes: [],
    created_at: now,
    dispatches: [l0],
  })
  await registerMockBatch(detail)
}

/** 一键初始化 C/D in_transit + E/F pending_pack 演示态 */
export async function initMockArrivalDemoState(
  scheduleCode: string = ARRIVAL_DEMO_SCHEDULE,
  nodeCode: string = ARRIVAL_DEMO_NODE,
): Promise<void> {
  if (scheduleCode !== ARRIVAL_DEMO_SCHEDULE) {
    throw new Error('Mock 演示仅支持方案 GS20260613001')
  }

  registerSchedulePackages(scheduleCode, [
    ARRIVAL_DEMO_PACKAGES.C,
    ARRIVAL_DEMO_PACKAGES.D,
    ARRIVAL_DEMO_PACKAGES.E,
    ARRIVAL_DEMO_PACKAGES.F,
  ])

  const demoPackages: PackageItem[] = [
    {
      package_code: ARRIVAL_DEMO_PACKAGES.C,
      weight: 12.5,
      volume: 0.45,
      status: 'in_transit',
      from_node_code: 'SC001',
      to_node_code: nodeCode,
      from_node_name: '华中仓储中心A',
      to_node_name: '一级分拣中心东湖',
      goods_items: [
        { goods_code: ARRIVAL_DEMO_PACKAGES.g1, order_code: ARRIVAL_DEMO_PACKAGES.order },
      ],
      created_at: '2026-06-13T10:00:00+08:00',
    },
    {
      package_code: ARRIVAL_DEMO_PACKAGES.D,
      weight: 8.2,
      volume: 0.32,
      status: 'in_transit',
      from_node_code: 'SC001',
      to_node_code: nodeCode,
      from_node_name: '华中仓储中心A',
      to_node_name: '一级分拣中心东湖',
      goods_items: [
        { goods_code: ARRIVAL_DEMO_PACKAGES.g2, order_code: ARRIVAL_DEMO_PACKAGES.order },
      ],
      created_at: '2026-06-13T10:00:00+08:00',
    },
    {
      package_code: ARRIVAL_DEMO_PACKAGES.E,
      weight: 5.0,
      volume: 0.18,
      status: 'pending_pack',
      from_node_code: nodeCode,
      to_node_code: 'SO001',
      from_node_name: '一级分拣中心东湖',
      to_node_name: '零级分拣站珞喻路',
      goods_items: [
        { goods_code: ARRIVAL_DEMO_PACKAGES.g1, order_code: ARRIVAL_DEMO_PACKAGES.order },
      ],
      created_at: '2026-06-13T10:00:00+08:00',
    },
    {
      package_code: ARRIVAL_DEMO_PACKAGES.F,
      weight: 6.8,
      volume: 0.22,
      status: 'pending_pack',
      from_node_code: nodeCode,
      to_node_code: 'SO001',
      from_node_name: '一级分拣中心东湖',
      to_node_name: '零级分拣站珞喻路',
      goods_items: [
        { goods_code: ARRIVAL_DEMO_PACKAGES.g2, order_code: ARRIVAL_DEMO_PACKAGES.order },
      ],
      created_at: '2026-06-13T10:00:00+08:00',
    },
  ]

  for (const pkg of demoPackages) {
    await upsertPackage(pkg)
  }

  const goods = await getMockGoods()
  for (const g of goods) {
    if (g.goods_code === ARRIVAL_DEMO_PACKAGES.g1) {
      g.status = 'in_transit'
      g.node_code = nodeCode
    }
    if (g.goods_code === ARRIVAL_DEMO_PACKAGES.g2) {
      g.status = 'in_transit'
      g.node_code = nodeCode
    }
  }

  const orders = await getMockOrders()
  const order = orders.find((o) => o.order_code === ARRIVAL_DEMO_PACKAGES.order)
  if (order) {
    order.status = 'delivering'
  }

  await syncScheduleDetailPackages(scheduleCode)
  await registerArrivalDemoBatch()
}

export async function getArrivalPackagesMock(
  params: GetArrivalPackagesParams,
): Promise<GetArrivalPackagesResult> {
  await delay(300)
  await ensureGoodsCache()
  const nodes = await getMockNodes()
  const node = nodes.find((n) => n.node_code === params.node_code)
  const packages = await getMockPackages()

  const items: ArrivalPackageItem[] = packages
    .filter(
      (p) =>
        p.status === 'in_transit' &&
        p.to_node_code === params.node_code &&
        packageBelongsToSchedule(params.schedule_code, p.package_code),
    )
    .map((p) => ({
      package_code: p.package_code,
      from_node_code: p.from_node_code,
      to_node_code: p.to_node_code,
      from_node_name: p.from_node_name,
      to_node_name: p.to_node_name,
      status: p.status,
      level_phase: 0,
      goods_items: p.goods_items.map((gi) => {
        const goods = goodsCache(gi.goods_code)
        return {
          goods_code: gi.goods_code,
          order_code: gi.order_code,
          goods_name: goods?.goods_name,
        }
      }),
    }))

  return {
    schedule_code: params.schedule_code,
    node_code: params.node_code,
    node_name: node?.name,
    packages: items,
  }
}

let cachedGoods: Awaited<ReturnType<typeof getMockGoods>> | null = null

function goodsCache(code: string) {
  return cachedGoods?.find((g) => g.goods_code === code)
}

async function ensureGoodsCache(): Promise<void> {
  cachedGoods = await getMockGoods()
}

function findDownstreamPackages(
  packages: PackageItem[],
  scheduleCode: string,
  nodeCode: string,
  goodsCode: string,
): PackageItem[] {
  return packages.filter(
    (p) =>
      packageBelongsToSchedule(scheduleCode, p.package_code) &&
      p.from_node_code === nodeCode &&
      p.status === 'pending_pack' &&
      p.goods_items.some((gi) => gi.goods_code === goodsCode),
  )
}

function cascadeExceptionPackages(
  packages: PackageItem[],
  scheduleCode: string,
  exceptionGoodsCodes: Set<string>,
): PackageItem[] {
  const affected: PackageItem[] = []
  for (const pkg of packages) {
    if (!packageBelongsToSchedule(scheduleCode, pkg.package_code)) continue
    if (pkg.status !== 'pending_pack' && pkg.status !== 'packed') continue
    const hit = pkg.goods_items.some((gi) => exceptionGoodsCodes.has(gi.goods_code))
    if (hit) {
      pkg.status = 'exception'
      affected.push(pkg)
    }
  }
  return affected
}

export async function confirmArrivalMock(
  payload: ConfirmArrivalPayload,
): Promise<ConfirmArrivalResult> {
  await delay(400)
  await ensureGoodsCache()
  const packages = await getMockPackages()
  const goods = await getMockGoods()
  const orders = await getMockOrders()

  const normalPackages: string[] = []
  const exceptionPackages: string[] = []
  const activatedDownstream: string[] = []
  const cascadeException: string[] = []
  const updatedGoods: ConfirmArrivalResult['updated_goods'] = []
  const updatedOrders: ConfirmArrivalResult['updated_orders'] = []

  const seen = new Set<string>()
  for (const item of payload.items) {
    if (seen.has(item.package_code)) {
      throw new Error('同一请求中重复包裹编号')
    }
    seen.add(item.package_code)

    const pkg = packages.find((p) => p.package_code === item.package_code)
    if (
      !pkg ||
      pkg.status !== 'in_transit' ||
      pkg.to_node_code !== payload.node_code ||
      !packageBelongsToSchedule(payload.schedule_code, pkg.package_code)
    ) {
      throw new Error(`包裹 ${item.package_code} 状态非 in_transit 或不属于该节点`)
    }

    if (item.result === 'normal') {
      pkg.status = 'delivered'
      normalPackages.push(pkg.package_code)

      for (const gi of pkg.goods_items) {
        const g = goods.find((x) => x.goods_code === gi.goods_code)
        if (!g) continue
        const order = orders.find((o) => o.order_code === gi.order_code)
        g.node_code = payload.node_code
        if (order && order.destination_node_code === payload.node_code) {
          g.status = 'delivered'
        } else {
          g.status = 'packed'
          const downstream = findDownstreamPackages(
            packages,
            payload.schedule_code,
            payload.node_code,
            g.goods_code,
          )
          for (const ds of downstream) {
            ds.status = 'packed'
            activatedDownstream.push(ds.package_code)
          }
        }
        updatedGoods.push({ goods_code: g.goods_code, status: g.status })
      }
    } else {
      pkg.status = 'exception'
      exceptionPackages.push(pkg.package_code)

      const exceptionGoods = new Set<string>()
      for (const gi of pkg.goods_items) {
        const g = goods.find((x) => x.goods_code === gi.goods_code)
        if (!g) continue
        g.status = 'exception'
        exceptionGoods.add(g.goods_code)
        updatedGoods.push({ goods_code: g.goods_code, status: g.status })
      }

      const cascaded = cascadeExceptionPackages(
        packages,
        payload.schedule_code,
        exceptionGoods,
      )
      for (const cp of cascaded) {
        cascadeException.push(cp.package_code)
      }

      for (const gi of pkg.goods_items) {
        const order = orders.find((o) => o.order_code === gi.order_code)
        if (order && order.status === 'delivering') {
          order.status = 'exception'
          updatedOrders.push({
            order_code: order.order_code,
            status: order.status,
          })
        }
      }
    }
  }

  await syncScheduleDetailPackages(payload.schedule_code)

  return {
    schedule_code: payload.schedule_code,
    node_code: payload.node_code,
    normal_packages: normalPackages,
    exception_packages: exceptionPackages,
    activated_downstream_packages: activatedDownstream,
    cascade_exception_packages: cascadeException,
    updated_goods: updatedGoods,
    updated_orders: updatedOrders,
  }
}

/** 注册演示方案包裹映射（页面加载时若未 init 则仅 GS20260613001 默认可查） */
export function ensureArrivalScheduleRegistry(scheduleCode: string): void {
  if (scheduleCode === ARRIVAL_DEMO_SCHEDULE && !schedulePackageRegistry.has(scheduleCode)) {
    registerSchedulePackages(
      scheduleCode,
      [ARRIVAL_DEMO_PACKAGES.C, ARRIVAL_DEMO_PACKAGES.D],
    )
  }
}
