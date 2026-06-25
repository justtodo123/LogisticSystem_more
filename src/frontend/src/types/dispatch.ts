export type BatchStatus = 'pending' | 'l0_l1_done' | 'completed' | 'failed'

export interface NodeDispatchCreatePayload {
  schedule_code: string
  demo_mode?: boolean
  simulate_failure?: 'no_packages' | 'no_vehicles' | 'first_phase_fail'
}

export interface NodeDispatchResult {
  batch_code: string
  status: BatchStatus
  l0_l1_dispatch_count: number
  l1_l2_dispatch_count: number
  route_codes?: string[]
  unallocated_packages?: string[]
}

/** 后端 API 返回的单车调度明细（扁平结构） */
export interface NodeDispatchItem {
  dispatch_code: string
  vehicle_code: string
  driver_code?: string | null
  level_phase: 0 | 1
  tasks: DispatchTask[]
  total_distance: number
  total_time?: number
}

export interface DispatchBatchSummary {
  batch_code: string
  schedule_code: string
  status: BatchStatus
  vehicle_count?: number
  l0_l1_dispatch_count?: number
  l1_l2_dispatch_count?: number
  demo_mode?: boolean
  created_at?: string
}

export interface DispatchPackageDetail {
  package_code: string
  weight?: number
  volume?: number
  goods_items?: Array<{
    goods_code: string
    goods_name?: string
    goods_type?: string
    order_code?: string
  }>
}

export interface DispatchTask {
  from_node_code: string
  to_node_code: string
  from_node_name?: string
  to_node_name?: string
  package_codes: string[]
  package_details?: DispatchPackageDetail[]
  is_return?: boolean
}

export interface VehicleDispatchItem {
  vehicle_code: string
  driver_code: string
  distance: number
  tasks: DispatchTask[]
}

export interface NodeDispatchPhase {
  level_phase: 0 | 1
  dispatch_code: string
  vehicle_tasks: VehicleDispatchItem[]
}

export interface DispatchBatchDetail extends DispatchBatchSummary {
  route_codes?: string[]
  unallocated_packages?: string[]
  /** API 为扁平列表；Mock 可在 normalize 前为分组结构 */
  dispatches: NodeDispatchItem[]
}
