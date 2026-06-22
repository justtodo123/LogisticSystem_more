export type PackageStatus =
  | 'pending_pack'
  | 'packed'
  | 'in_transit'
  | 'delivered'
  | 'exception'

export interface PackageGoodsItem {
  goods_code: string
  order_code?: string
}

export interface PackageItem {
  package_code: string
  weight: number
  volume: number
  status: PackageStatus
  from_node_code: string
  to_node_code: string
  from_node_name?: string
  to_node_name?: string
  goods_items: PackageGoodsItem[]
  created_at?: string
  updated_at?: string
}

export interface PackageDetail extends PackageItem {
  from_longitude?: number | null
  from_latitude?: number | null
  to_longitude?: number | null
  to_latitude?: number | null
  dispatch_code?: string | null
}
