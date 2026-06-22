import type { DispatchBatchDetail, NodeDispatchItem } from '@/types/dispatch'
import type {
  SimulationDeliverPayload,
  SimulationDeliverResult,
} from '@/types/simulation'
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

function collectCargoPackageCodes(
  dispatches: NodeDispatchItem[],
  levelPhase: 0 | 1,
): string[] {
  const codes = new Set<string>()
  for (const d of dispatches) {
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

function collectPackagesByVehicle(
  dispatches: NodeDispatchItem[],
  vehicleCode: string,
): string[] {
  const codes = new Set<string>()
  const dispatch = dispatches.find((d) => d.vehicle_code === vehicleCode)
  if (!dispatch) return []
  for (const task of dispatch.tasks) {
    if (task.is_return) continue
    for (const pkg of task.package_codes) {
      codes.add(pkg)
    }
  }
  return [...codes]
}

function resolveTargetPackageCodes(
  batch: DispatchBatchDetail,
  payload: SimulationDeliverPayload,
): string[] {
  const levelPhase: 0 | 1 = batch.status === 'pending' ? 0 : 1
  let codes = collectCargoPackageCodes(batch.dispatches, levelPhase)

  if (payload.package_code) {
    codes = codes.filter((c) => c === payload.package_code)
  } else if (payload.vehicle_code) {
    const vehicleCodes = collectPackagesByVehicle(
      batch.dispatches,
      payload.vehicle_code,
    )
    codes = codes.filter((c) => vehicleCodes.includes(c))
  }

  return codes
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

  batch.status = 'l0_l1_done'
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
  const batches = await getMockBatches()
  const batchCode =
    payload.batch_code ??
    batches.find((b) => b.status !== 'completed')?.batch_code

  if (!batchCode) {
    throw new Error('无可用调度批次，请先生成节点间调度')
  }

  const batch = await getMockBatchDetail(batchCode)
  if (!batch) {
    throw new Error('调度批次不存在')
  }
  if (batch.status === 'completed') {
    throw new Error('该批次已完成，无需模拟送达')
  }

  const targetCodes = resolveTargetPackageCodes(batch, payload)
  const packages = await getMockPackages()
  const deliverable = targetCodes.filter((code) => {
    const pkg = packages.find((p) => p.package_code === code)
    return pkg?.status === 'in_transit'
  })

  if (!deliverable.length) {
    throw new Error('无运输中包裹可送达')
  }

  let count = 0
  if (batch.status === 'pending') {
    count = await applyL0Delivery(batch, deliverable)
  } else if (batch.status === 'l0_l1_done') {
    count = await applyL1Delivery(batch, deliverable)
  } else {
    throw new Error('当前批次状态不支持模拟送达')
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
  if (!batch || batch.status === 'completed') return 0
  const levelPhase: 0 | 1 = batch.status === 'pending' ? 0 : 1
  const codes = collectCargoPackageCodes(batch.dispatches, levelPhase)
  const packages = await getMockPackages()
  return codes.filter((code) => {
    const pkg = packages.find((p) => p.package_code === code)
    return pkg?.status === 'in_transit'
  }).length
}
