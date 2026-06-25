import request from './request'
import { listPackages } from './packages'
import type {
  ArrivalPackageItem,
  ConfirmArrivalPayload,
  ConfirmArrivalResult,
  GetArrivalPackagesParams,
  GetArrivalPackagesResult,
  SimulationDeliverPayload,
  SimulationDeliverResponse,
  SimulationDeliverResult,
} from '@/types/simulation'
import { useMockSimulation } from '@/utils/env'
import {
  confirmArrivalMock,
  getArrivalPackagesMock,
} from '@/utils/mock-arrival-store'
import { simulateDeliverMock } from '@/utils/mock-simulation'

/** 后端 GET /arrival-packages 返回的单条记录 */
interface BackendArrivalPackageRow {
  package_code: string
  schedule_code?: string
  from_node_code: string
  to_node_code: string
  status: string
  arrived_at?: string | null
}

/** 后端 POST /confirm-arrival-batch 响应 */
interface BackendBatchConfirmResultItem {
  package_code: string
  status: string
  goods_status?: string
  order_status?: string
  triggered_repacking?: boolean
  new_package_code?: string | null
}

interface BackendBatchConfirmResponse {
  total: number
  success_count: number
  failed_count: number
  results?: BackendBatchConfirmResultItem[]
  errors?: Array<{ package_code?: string; message?: string }>
}

function compactPayload(
  payload: SimulationDeliverPayload,
): Omit<SimulationDeliverPayload, 'batch_code'> {
  const body: Omit<SimulationDeliverPayload, 'batch_code'> = {}
  if (payload.vehicle_code) body.vehicle_code = payload.vehicle_code
  if (payload.package_code) body.package_code = payload.package_code
  return body
}

function toResult(data: SimulationDeliverResponse): SimulationDeliverResult {
  const count = data.delivered_package_codes.length
  return {
    packages_delivered: count,
    delivered_package_codes: data.delivered_package_codes,
    message:
      count > 0
        ? `已模拟送达 ${count} 个包裹`
        : '未送达包裹',
  }
}

async function enrichArrivalPackages(
  rows: BackendArrivalPackageRow[],
): Promise<ArrivalPackageItem[]> {
  if (rows.length === 0) return []

  const codes = new Set(rows.map((r) => r.package_code))
  const goodsByPackage = new Map<
    string,
    ArrivalPackageItem['goods_items']
  >()

  try {
    const result = await listPackages({ page: 1, page_size: 500 })
    for (const pkg of result.items) {
      if (codes.has(pkg.package_code)) {
        goodsByPackage.set(
          pkg.package_code,
          pkg.goods_items.map((gi) => ({
            goods_code: gi.goods_code,
            order_code: gi.order_code,
          })),
        )
      }
    }
  } catch {
    // 补全失败不阻塞列表展示
  }

  return rows.map((row) => ({
    package_code: row.package_code,
    from_node_code: row.from_node_code,
    to_node_code: row.to_node_code,
    status: row.status,
    goods_items: goodsByPackage.get(row.package_code) ?? [],
  }))
}

function mapBatchConfirmResponse(
  payload: ConfirmArrivalPayload,
  data: BackendBatchConfirmResponse,
): ConfirmArrivalResult {
  const results = data.results ?? []
  const normalPackages: string[] = []
  const exceptionPackages: string[] = []
  const activatedDownstream: string[] = []
  const updatedGoods: ConfirmArrivalResult['updated_goods'] = []
  const updatedOrders: ConfirmArrivalResult['updated_orders'] = []

  for (const item of results) {
    if (item.status === 'exception') {
      exceptionPackages.push(item.package_code)
    } else {
      normalPackages.push(item.package_code)
    }
    if (item.triggered_repacking && item.new_package_code) {
      activatedDownstream.push(item.new_package_code)
    }
    if (item.goods_status) {
      updatedGoods.push({ goods_code: item.package_code, status: item.goods_status })
    }
    if (item.order_status) {
      updatedOrders.push({ order_code: item.package_code, status: item.order_status })
    }
  }

  return {
    schedule_code: payload.schedule_code,
    node_code: payload.node_code,
    normal_packages: normalPackages,
    exception_packages: exceptionPackages,
    activated_downstream_packages: activatedDownstream,
    cascade_exception_packages: [],
    updated_goods: updatedGoods,
    updated_orders: updatedOrders,
  }
}

export async function simulateDeliver(
  payload: SimulationDeliverPayload = {},
): Promise<SimulationDeliverResult> {
  if (useMockSimulation()) {
    return simulateDeliverMock(payload)
  }
  const { data } = await request.post<SimulationDeliverResponse>(
    '/simulation/deliver',
    compactPayload(payload),
  )
  return toResult(data)
}

export async function getArrivalPackages(
  params: GetArrivalPackagesParams,
): Promise<GetArrivalPackagesResult> {
  if (useMockSimulation()) {
    return getArrivalPackagesMock(params)
  }
  const { data } = await request.get<
    BackendArrivalPackageRow[] | GetArrivalPackagesResult
  >('/simulation/arrival-packages', { params })

  const rows: BackendArrivalPackageRow[] = Array.isArray(data)
    ? data
    : (data.packages ?? [])

  const packages = await enrichArrivalPackages(rows)

  return {
    schedule_code: params.schedule_code,
    node_code: params.node_code,
    packages,
  }
}

export async function confirmArrival(
  payload: ConfirmArrivalPayload,
): Promise<ConfirmArrivalResult> {
  if (useMockSimulation()) {
    return confirmArrivalMock(payload)
  }
  const { data } = await request.post<BackendBatchConfirmResponse>(
    '/simulation/confirm-arrival-batch',
    {
      schedule_code: payload.schedule_code,
      confirmations: payload.items.map((item) => ({
        package_code: item.package_code,
        is_normal: item.result === 'normal',
        ...(item.result === 'exception' && item.exception_subtype
          ? { exception_subtype: item.exception_subtype }
          : {}),
        ...(item.remark ? { remark: item.remark } : {}),
      })),
    },
  )
  return mapBatchConfirmResponse(payload, data)
}
