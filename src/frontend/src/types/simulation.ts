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

export type ArrivalConfirmResult = 'normal' | 'exception'

export type PackageArrivalExceptionSubtype =
  | 'damaged'
  | 'lost'
  | 'delayed'
  | 'other'

export interface ArrivalPackageGoodsItem {
  goods_code: string
  order_code?: string
  goods_name?: string
}

export interface ArrivalPackageItem {
  package_code: string
  from_node_code: string
  to_node_code: string
  from_node_name?: string
  to_node_name?: string
  status: string
  level_phase?: number
  goods_items: ArrivalPackageGoodsItem[]
}

export interface GetArrivalPackagesParams {
  schedule_code: string
  node_code: string
}

export interface GetArrivalPackagesResult {
  schedule_code: string
  node_code: string
  node_name?: string
  packages: ArrivalPackageItem[]
}

export interface ConfirmArrivalItem {
  package_code: string
  result: ArrivalConfirmResult
  exception_subtype?: string
  remark?: string
}

export interface ConfirmArrivalPayload {
  schedule_code: string
  node_code: string
  items: ConfirmArrivalItem[]
}

export interface ConfirmArrivalStatusUpdate {
  goods_code?: string
  order_code?: string
  status: string
}

export interface ConfirmArrivalResult {
  schedule_code: string
  node_code: string
  normal_packages: string[]
  exception_packages: string[]
  activated_downstream_packages: string[]
  cascade_exception_packages: string[]
  updated_goods: ConfirmArrivalStatusUpdate[]
  updated_orders: ConfirmArrivalStatusUpdate[]
}
