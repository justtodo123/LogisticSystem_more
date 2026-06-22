import type { NodeDispatchItem } from '@/types/dispatch'

export interface RouteNodePoint {
  node_code: string
  latitude: number
  longitude: number
  role?: string
}

export interface RoutePackagePoint {
  package_code: string
  latitude: number
  longitude: number
}

export interface RouteSegment {
  road_name: string
  start_lng: number
  start_lat: number
  end_lng: number
  end_lat: number
}

export interface RouteCoordinates {
  vehicle_code: string
  route_code: string
  nodes: RouteNodePoint[]
  packages: RoutePackagePoint[]
  segments: RouteSegment[]
  total_distance: number
  total_time: number
}

export interface SelectedPackageDetail {
  package_code: string
  route_code: string
  from_node_code?: string
  to_node_code?: string
  total_distance?: number
  total_time?: number
}

/** 后端 GET /routes/by-vehicle/{code}/coordinates 响应 data */
export interface BackendRouteCoordinate {
  route_code: string
  batch_code: string | null
  coordinates: [number, number][]
  total_distance: number
}

export interface BackendRouteCoordinatesResponse {
  vehicle_code: string
  routes: BackendRouteCoordinate[]
}

/** 后端 GET /routes/{route_code} 响应 data */
export interface RouteDetailResponse {
  route_code: string
  batch_code: string | null
  dispatch_code: string | null
  vehicle_code: string
  route_segments: RouteSegment[]
  total_distance: number
  total_time: number
  total_emission?: number
  algorithm_type?: string
  created_at?: string
}

export interface GetVehicleRouteOptions {
  batchCode?: string
  dispatch?: NodeDispatchItem | null
}

export interface RoutePlanRequest {
  batch_code: string
  dispatch_codes?: string[] | null
}

export interface RoutePlanItem {
  route_code: string
  vehicle_code: string
  total_distance: number
  total_time: number
}

export interface RoutePlanResult {
  batch_code: string
  status: string
  routes: RoutePlanItem[]
}

export interface RouteListItem {
  route_code: string
  batch_code?: string | null
  vehicle_code?: string
  total_distance?: number
}
