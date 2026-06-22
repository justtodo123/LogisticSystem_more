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
}

export interface DispatchBatchSummary {
  batch_code: string
  schedule_code: string
  status: BatchStatus
  vehicle_count: number
  l0_l1_dispatch_count?: number
  l1_l2_dispatch_count?: number
  created_at?: string
}

export interface DispatchTask {
  from_node_code: string
  to_node_code: string
  package_codes: string[]
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
  dispatches: NodeDispatchPhase[]
}
