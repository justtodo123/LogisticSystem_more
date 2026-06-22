export type OrderStatus = 'pending' | 'delivering' | 'completed' | 'exception'

export interface Order {
  order_code: string
  destination_node_code: string
  destination_node_name?: string
  time_window: string
  status: OrderStatus
  goods_count?: number
  created_at: string
  updated_at?: string
}

export interface OrderGoodsItem {
  goods_code: string
  goods_name: string
  goods_type: string
  weight: number
  volume: number
  status: string
}

export interface OrderDetail extends Order {
  goods: OrderGoodsItem[]
}

export interface OrderGoodsCreateItem {
  goods_name: string
  goods_type: string
  weight: number
  volume: number
}

export interface OrderCreatePayload {
  order_code?: string
  destination_node_code: string
  time_window: string
  goods: OrderGoodsCreateItem[]
}

export interface OrderUpdatePayload {
  destination_node_code?: string
  time_window?: string
}

export interface OrderImportResult {
  success_count: number
  fail_count: number
  errors?: string[]
}
