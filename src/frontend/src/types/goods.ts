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
  node_name?: string
  order_code: string
  status: GoodsStatus
  created_at?: string
  updated_at?: string
}

export interface GoodsDetail extends Goods {
  node_name: string
}
