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
