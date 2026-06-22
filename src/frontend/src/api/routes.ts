import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type {
  RouteCoordinates,
  RouteDetailResponse,
  GetVehicleRouteOptions,
  RouteListItem,
  RoutePlanResult,
} from '@/types/route'
import { useMockRoutes } from '@/utils/env'
import { buildMockRouteCoordinates } from '@/utils/mock-route-builder'
import { normalizeFromRouteDetail } from '@/utils/route-normalize'
import { listMockRoutes } from '@/utils/mock-exception-store'

let staticMockCache: Record<string, RouteCoordinates> | null = null

interface RouteListResponse {
  items: RouteListItem[]
  total: number
}

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

export async function listRoutes(
  params: ApiListParams & { batch_code?: string; vehicle_code?: string } = {},
): Promise<PaginatedResult<RouteListItem>> {
  if (useMockRoutes()) {
    return listMockRoutes(params)
  }

  const { data } = await request.get<RouteListResponse>('/routes', { params })
  return data
}

export async function getRouteDetail(routeCode: string): Promise<RouteDetailResponse> {
  const { data } = await request.get<RouteDetailResponse>(
    `/routes/${encodeURIComponent(routeCode)}`,
  )
  return data
}

export async function planRoutes(batchCode: string): Promise<RoutePlanResult> {
  const { data } = await request.post<RoutePlanResult>('/routes/plan', {
    batch_code: batchCode,
  })
  return data
}

export async function getVehicleRouteCoordinates(
  vehicleCode: string,
  options?: GetVehicleRouteOptions,
): Promise<RouteCoordinates> {
  const dispatch = options?.dispatch ?? null

  if (useMockRoutes()) {
    if (dispatch?.tasks?.length) {
      return buildMockRouteCoordinates(vehicleCode, dispatch)
    }
    const cache = await loadStaticMockCache()
    const fallback = cache[vehicleCode]
    if (fallback) return fallback
    throw new Error('该车辆暂无路线，请先生成节点间调度')
  }

  const { data: listData } = await request.get<RouteListResponse>('/routes', {
    params: {
      vehicle_code: vehicleCode,
      batch_code: options?.batchCode,
      page: 1,
      page_size: 1,
    },
  })

  if (!listData.items?.length) {
    throw new Error('该车辆暂无路线，请先完成路径规划')
  }

  const detail = await getRouteDetail(listData.items[0].route_code)
  return normalizeFromRouteDetail(vehicleCode, detail, dispatch)
}
