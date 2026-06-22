import type { DispatchBatchDetail } from '@/types/dispatch'
import type { NodeDispatchItem } from '@/types/dispatch'

export const MAX_ROUTE_VEHICLES = 10

export interface RouteVehicleOption {
  vehicle_code: string
  dispatch: NodeDispatchItem
}

export function listRouteVehicles(
  batchDetail: DispatchBatchDetail | null,
): RouteVehicleOption[] {
  if (!batchDetail?.dispatches?.length) return []

  const map = new Map<string, NodeDispatchItem>()
  for (const d of batchDetail.dispatches) {
    if (!map.has(d.vehicle_code)) {
      map.set(d.vehicle_code, d)
    }
  }
  return [...map.entries()].map(([vehicle_code, dispatch]) => ({
    vehicle_code,
    dispatch,
  }))
}
