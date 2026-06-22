import type { DispatchBatchDetail, NodeDispatchItem } from '@/types/dispatch'

export function collectCargoPackageCodes(
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

export function collectAllCargoPackageCodes(
  batch: DispatchBatchDetail,
): string[] {
  const codes = new Set<string>()
  for (const phase of [0, 1] as const) {
    for (const code of collectCargoPackageCodes(batch.dispatches, phase)) {
      codes.add(code)
    }
  }
  return [...codes]
}

export function collectPackagesByVehicle(
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

export function filterInTransitCodes(
  codes: string[],
  isInTransit: (code: string) => boolean,
): string[] {
  return codes.filter(isInTransit)
}

export function resolveActiveDeliveryPhase(
  batch: DispatchBatchDetail,
  isInTransit: (code: string) => boolean,
): 0 | 1 | null {
  const l0 = collectCargoPackageCodes(batch.dispatches, 0)
  if (filterInTransitCodes(l0, isInTransit).length > 0) {
    return 0
  }
  const l1 = collectCargoPackageCodes(batch.dispatches, 1)
  if (filterInTransitCodes(l1, isInTransit).length > 0) {
    return 1
  }
  return null
}

export function resolveTargetPackageCodes(
  batch: DispatchBatchDetail,
  payload: { vehicle_code?: string; package_code?: string },
  isInTransit: (code: string) => boolean,
): string[] {
  const phase = resolveActiveDeliveryPhase(batch, isInTransit)
  if (phase === null) return []

  let codes = collectCargoPackageCodes(batch.dispatches, phase)

  if (payload.package_code) {
    codes = codes.filter((c) => c === payload.package_code)
  } else if (payload.vehicle_code) {
    const vehicleCodes = collectPackagesByVehicle(
      batch.dispatches,
      payload.vehicle_code,
    )
    codes = codes.filter((c) => vehicleCodes.includes(c))
  }

  return filterInTransitCodes(codes, isInTransit)
}
