import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type {
  Order,
  OrderCreatePayload,
  OrderDetail,
  OrderImportResult,
  OrderUpdatePayload,
} from '@/types/order'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate, nextCode } from '@/utils/mock'
import { getMockGoods, getMockNodes, getMockOrders } from '@/utils/mock-store'

async function enrichOrder(order: Order): Promise<Order> {
  if (order.destination_node_name) return order
  const nodes = await getMockNodes()
  const node = nodes.find((n) => n.node_code === order.destination_node_code)
  return {
    ...order,
    destination_node_name: node?.name ?? order.destination_node_code,
  }
}

export async function listOrders(
  params: ApiListParams = {},
): Promise<PaginatedResult<Order>> {
  if (useMockBasicData()) {
    const orders = await getMockOrders()
    const result = filterAndPaginate(orders, params, (item, p) => {
      if (p.status && item.status !== p.status) return false
      const dest = p.destination_node_code as string | undefined
      if (dest && item.destination_node_code !== dest) return false
      return true
    })
    const items = await Promise.all(result.items.map(enrichOrder))
    return { ...result, items }
  }
  const { data } = await request.get<PaginatedResult<Order>>('/orders', {
    params,
  })
  return data
}

export async function getOrder(orderCode: string): Promise<OrderDetail> {
  if (useMockBasicData()) {
    const orders = await getMockOrders()
    const order = orders.find((o) => o.order_code === orderCode)
    if (!order) throw new Error('订单不存在')
    const enriched = await enrichOrder(order)
    const goods = await getMockGoods()
    return {
      ...enriched,
      updated_at: enriched.updated_at ?? enriched.created_at,
      goods: goods
        .filter((g) => g.order_code === orderCode)
        .map((g) => ({
          goods_code: g.goods_code,
          goods_name: g.goods_name,
          goods_type: g.goods_type,
          weight: g.weight,
          volume: g.volume,
          status: g.status,
        })),
    }
  }
  const { data } = await request.get<OrderDetail>(
    `/orders/${encodeURIComponent(orderCode)}`,
  )
  return data
}

export async function createOrder(payload: OrderCreatePayload): Promise<Order> {
  if (useMockBasicData()) {
    const orders = await getMockOrders()
    const nodes = await getMockNodes()
    const dest = nodes.find((n) => n.node_code === payload.destination_node_code)
    if (!dest || dest.node_type !== 'sorting_center' || dest.level !== 0) {
      throw new Error('目的地必须为 0 级分拣中心')
    }
    if (!payload.goods?.length) {
      throw new Error('至少添加一条货物')
    }
    const order: Order = {
      order_code:
        payload.order_code ||
        nextCode(
          'O20260612',
          orders.map((o) => o.order_code),
        ),
      destination_node_code: payload.destination_node_code,
      destination_node_name: dest.name,
      time_window: payload.time_window,
      status: 'pending',
      created_at: new Date().toISOString(),
    }
    orders.unshift(order)
    return order
  }
  const { data } = await request.post<Order>('/orders', {
    destination_node_code: payload.destination_node_code,
    time_window: payload.time_window,
    goods: payload.goods,
  })
  return data
}

export async function updateOrder(
  orderCode: string,
  payload: OrderUpdatePayload,
): Promise<Order> {
  if (useMockBasicData()) {
    const orders = await getMockOrders()
    const idx = orders.findIndex((o) => o.order_code === orderCode)
    if (idx < 0) throw new Error('订单不存在')
    if (orders[idx].status !== 'pending') {
      throw new Error('仅待分配订单可编辑')
    }
    if (payload.destination_node_code) {
      const nodes = await getMockNodes()
      const dest = nodes.find(
        (n) => n.node_code === payload.destination_node_code,
      )
      if (!dest || dest.node_type !== 'sorting_center' || dest.level !== 0) {
        throw new Error('目的地必须为 0 级分拣中心')
      }
      orders[idx].destination_node_name = dest.name
    }
    orders[idx] = { ...orders[idx], ...payload }
    return orders[idx]
  }
  const { data } = await request.put<Order>(`/orders/${orderCode}`, payload)
  return data
}

export async function deleteOrder(orderCode: string): Promise<void> {
  if (useMockBasicData()) {
    const orders = await getMockOrders()
    const idx = orders.findIndex((o) => o.order_code === orderCode)
    if (idx < 0) throw new Error('订单不存在')
    if (orders[idx].status !== 'pending') {
      throw new Error('配送中或已完成的订单不可删除')
    }
    orders.splice(idx, 1)
    return
  }
  await request.delete(`/orders/${orderCode}`)
}

export async function importOrders(file: File): Promise<OrderImportResult> {
  if (useMockBasicData()) {
    await new Promise((r) => setTimeout(r, 500))
    return {
      success_count: Math.max(1, Math.floor(file.size / 100)),
      fail_count: 0,
      errors: [],
    }
  }
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await request.post<{
    success_count: number
    failed_count: number
    failed_rows?: Array<Record<string, unknown>>
  }>('/orders/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return {
    success_count: data.success_count,
    fail_count: data.failed_count,
    errors: data.failed_rows?.map((row) => JSON.stringify(row)),
  }
}
