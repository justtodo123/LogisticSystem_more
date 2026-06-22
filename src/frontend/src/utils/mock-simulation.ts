import type { DispatchBatchDetail } from '@/types/dispatch'
import type {
  SimulationDeliverPayload,
  SimulationDeliverResult,
} from '@/types/simulation'
import {
  collectAllCargoPackageCodes,
  filterInTransitCodes,
  resolveActiveDeliveryPhase,
  resolveTargetPackageCodes,
} from '@/utils/simulation-batch-utils'
import {
  getMockBatchDetail,
  getMockBatches,
  getMockDrivers,
  getMockGoods,
  getMockPackages,
  getMockVehicles,
  updateMockBatchDetail,
  updateMockBatchSummary,
} from '@/utils/mock-store'

async function resolveMockBatchCode(
  payload: SimulationDeliverPayload,
): Promise<string | null> {
  if (payload.batch_code) {
    return payload.batch_code
  }
  const batches = await getMockBatches()
  for (const summary of batches) {
    const detail = await getMockBatchDetail(summary.batch_code)
    if (!detail) continue
    const count = await countInTransitPackagesInBatch(detail)
    if (count > 0) {
      return summary.batch_code
    }
  }
  return batches[0]?.batch_code ?? null
}

async function applyL0Delivery(
  batch: DispatchBatchDetail,
  packageCodes: string[],
): Promise<number> {
  const packages = await getMockPackages()
  const goods = await getMockGoods()
  const vehicles = await getMockVehicles()
  const drivers = await getMockDrivers()
  let count = 0

  const vehicleCodes = new Set(
    batch.dispatches
      .filter((d) => d.level_phase === 0)
      .map((d) => d.vehicle_code),
  )

  for (const code of packageCodes) {
    const pkg = packages.find((p) => p.package_code === code)
    if (!pkg || pkg.status !== 'in_transit') continue
    pkg.status = 'delivered'
    count += 1
    for (const item of pkg.goods_items) {
      const g = goods.find((x) => x.goods_code === item.goods_code)
      if (g && g.status === 'in_transit') {
        g.status = 'pending_pack'
      }
    }
  }

  for (const v of vehicles) {
    if (vehicleCodes.has(v.vehicle_code) && v.status === 'delivering') {
      v.status = 'idle'
    }
  }
  for (const d of drivers) {
    const linked = batch.dispatches.some(
      (disp) => disp.driver_code === d.driver_code && disp.level_phase === 0,
    )
    if (linked && d.status === 'busy') {
      d.status = 'idle'
    }
  }

  if (batch.status === 'pending') {
    batch.status = 'l0_l1_done'
  }
  return count
}

async function applyL1Delivery(
  batch: DispatchBatchDetail,
  packageCodes: string[],
): Promise<number> {
  const packages = await getMockPackages()
  const goods = await getMockGoods()
  const vehicles = await getMockVehicles()
  const drivers = await getMockDrivers()
  let count = 0

  const vehicleCodes = new Set(
    batch.dispatches
      .filter((d) => d.level_phase === 1)
      .map((d) => d.vehicle_code),
  )

  for (const code of packageCodes) {
    const pkg = packages.find((p) => p.package_code === code)
    if (!pkg || pkg.status !== 'in_transit') continue
    pkg.status = 'delivered'
    count += 1
    for (const item of pkg.goods_items) {
      const g = goods.find((x) => x.goods_code === item.goods_code)
      if (g && g.status === 'in_transit') {
        g.status = 'delivered'
      }
    }
  }

  for (const v of vehicles) {
    if (vehicleCodes.has(v.vehicle_code) && v.status === 'delivering') {
      v.status = 'idle'
    }
  }
  for (const d of drivers) {
    const linked = batch.dispatches.some(
      (disp) => disp.driver_code === d.driver_code && disp.level_phase === 1,
    )
    if (linked && d.status === 'busy') {
      d.status = 'idle'
    }
  }

  batch.status = 'completed'
  return count
}

export async function simulateDeliverMock(
  payload: SimulationDeliverPayload = {},
): Promise<SimulationDeliverResult> {
  const batchCode = await resolveMockBatchCode(payload)

  if (!batchCode) {
    throw new Error('无可用调度批次，请先生成节点间调度')
  }

  const batch = await getMockBatchDetail(batchCode)
  if (!batch) {
    throw new Error('调度批次不存在')
  }

  const packages = await getMockPackages()
  const isInTransit = (code: string): boolean =>
    packages.find((p) => p.package_code === code)?.status === 'in_transit'

  const targetCodes = resolveTargetPackageCodes(batch, payload, isInTransit)
  const deliverable = filterInTransitCodes(targetCodes, isInTransit)

  if (!deliverable.length) {
    throw new Error('无运输中包裹可送达')
  }

  const phase = resolveActiveDeliveryPhase(batch, isInTransit)
  if (phase === null) {
    throw new Error('无运输中包裹可送达')
  }

  let count = 0
  if (phase === 0) {
    count = await applyL0Delivery(batch, deliverable)
  } else {
    count = await applyL1Delivery(batch, deliverable)
  }

  await updateMockBatchDetail(batch)
  await updateMockBatchSummary(batch)

  return {
    packages_delivered: count,
    delivered_package_codes: deliverable,
    message: `已模拟送达 ${count} 个包裹`,
  }
}

export async function countInTransitPackagesInBatch(
  batch: DispatchBatchDetail | null,
): Promise<number> {
  if (!batch || batch.status === 'failed') return 0

  const packages = await getMockPackages()
  const isInTransit = (code: string): boolean =>
    packages.find((p) => p.package_code === code)?.status === 'in_transit'

  const codes = collectAllCargoPackageCodes(batch)
  return filterInTransitCodes(codes, isInTransit).length
}
