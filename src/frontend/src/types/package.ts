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
  goods_items: PackageGoodsItem[]
  created_at?: string
}
