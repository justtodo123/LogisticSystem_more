export type GoodsStatus =
  | 'pending_pack'
  | 'packed'
  | 'in_transit'
  | 'delivered'
  | 'exception'

export interface Goods {
  goods_code: string
  goods_name: string
  goods_type: string
  weight: number
  volume: number
  node_code: string
  order_code: string
  status: GoodsStatus
  created_at?: string
}
