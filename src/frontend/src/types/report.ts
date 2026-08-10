/** T5-3 报表分析 - 类型定义 */

export interface SlaReport {
  date_from: string | null
  date_to: string | null
  total_orders: number
  signed_orders: number
  in_progress_orders: number
  exception_orders: number
  on_time_rate: number
  avg_delay_minutes: number
  sla_target_hours: number
}

export interface CostVehicleItem {
  vehicle_code: string
  distance_km: number
  cost: number
  route_count: number
}

export interface CostNodeItem {
  node_code: string
  cost: number
  route_count: number
}

export interface CostReport {
  total_cost: number
  by_vehicle: CostVehicleItem[]
  by_node: CostNodeItem[]
}

export interface ExceptionCountItem {
  type?: string
  count: number
}

export interface ExceptionSubtypeCountItem {
  subtype?: string
  count: number
}

export interface ExceptionReport {
  total_exceptions: number
  open_count: number
  resolved_count: number
  by_type: ExceptionCountItem[]
  by_subtype: ExceptionSubtypeCountItem[]
}

export interface CapacityReport {
  total_vehicles: number
  idle_count: number
  delivering_count: number
  dispatch_count: number
  package_count: number
  delivered_package_count: number
  avg_distance_km: number
}

export interface ReportOverview {
  sla: SlaReport
  cost: CostReport
  exceptions: ExceptionReport
  capacity: CapacityReport
}
