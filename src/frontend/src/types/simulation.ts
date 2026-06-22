export interface SimulationDeliverPayload {
  /** Mock 联调辅助；真实 API 契约不含此字段 */
  batch_code?: string
  vehicle_code?: string
  package_code?: string
}

/** 后端 DeliverResponse（api-contract-phase6 §3.2） */
export interface SimulationDeliverResponse {
  delivered_package_codes: string[]
  status_changed_goods_count: number
  updated_order_count: number
  delivered_order_codes: string[]
  level_info?: {
    l0_to_l1?: number
    l1_to_l2?: number
  }
}

/** UI 层统一结果 */
export interface SimulationDeliverResult {
  packages_delivered: number
  delivered_package_codes: string[]
  message?: string
}
