export const ORDER_STATUSES = [
  'unassigned',
  'assigned',
  'in_transit',
  'signed',
  'exception',
  'closed',
] as const

export type OrderStatus = (typeof ORDER_STATUSES)[number]

export const LEGACY_ORDER_STATUS_MAP = {
  pending: 'unassigned',
  delivering: 'in_transit',
  completed: 'signed',
} as const

export const ORDER_STATUS_CONTRACT_VERSION = '2026-08-19-six-state'

export function isOrderStatus(value: string): value is OrderStatus {
  return (ORDER_STATUSES as readonly string[]).includes(value)
}

export function migrateLegacyOrderStatusValue(value: string): string {
  return (
    LEGACY_ORDER_STATUS_MAP[value as keyof typeof LEGACY_ORDER_STATUS_MAP] ??
    value
  )
}

export const ORDER_MUTABLE_STATUSES: readonly OrderStatus[] = [
  'unassigned',
  'assigned',
]

export const ORDER_CLOSABLE_STATUSES: readonly OrderStatus[] = [
  'unassigned',
  'assigned',
]

export function canMutateOrder(status: string): boolean {
  return (ORDER_MUTABLE_STATUSES as readonly string[]).includes(status)
}

export function canCloseOrder(status: string): boolean {
  return (ORDER_CLOSABLE_STATUSES as readonly string[]).includes(status)
}

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
