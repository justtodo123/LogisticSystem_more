import request from './request'
import type { NodeDispatchItem } from '@/types/dispatch'
import type { RouteCoordinates } from '@/types/route'
import { useMockRoutes } from '@/utils/env'
import { buildMockRouteCoordinates } from '@/utils/mock-route-builder'

let staticMockCache: Record<string, RouteCoordinates> | null = null

async function loadStaticMockCache(): Promise<Record<string, RouteCoordinates>> {
  if (staticMockCache) return staticMockCache
  const res = await fetch('/mock/route-coordinates.json')
  if (!res.ok) {
    staticMockCache = {}
    return staticMockCache
  }
  staticMockCache = (await res.json()) as Record<string, RouteCoordinates>
  return staticMockCache
}

export async function getVehicleRouteCoordinates(
  vehicleCode: string,
  dispatch?: NodeDispatchItem | null,
): Promise<RouteCoordinates> {
  if (useMockRoutes()) {
    if (dispatch?.tasks?.length) {
      return buildMockRouteCoordinates(vehicleCode, dispatch)
    }
    const cache = await loadStaticMockCache()
    const fallback = cache[vehicleCode]
    if (fallback) return fallback
    throw new Error('该车辆暂无路线，请先生成节点间调度')
  }

  const { data } = await request.get<RouteCoordinates>(
    `/routes/by-vehicle/${encodeURIComponent(vehicleCode)}/coordinates`,
  )
  return data
}
