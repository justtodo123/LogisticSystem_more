import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { Goods, GoodsDetail } from '@/types/goods'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockGoods, getMockNodes } from '@/utils/mock-store'

export async function listGoods(
  params: ApiListParams = {},
): Promise<PaginatedResult<Goods>> {
  if (useMockBasicData()) {
    const goods = await getMockGoods()
    return filterAndPaginate(goods, params, (item, p) => {
      if (p.status && item.status !== p.status) return false
      if (p.order_code && item.order_code !== p.order_code) return false
      if (p.node_code && item.node_code !== p.node_code) return false
      return true
    })
  }
  const { data } = await request.get<PaginatedResult<Goods>>('/goods', {
    params,
  })
  return data
}

export async function getGoods(goodsCode: string): Promise<GoodsDetail> {
  if (useMockBasicData()) {
    const goods = await getMockGoods()
    const item = goods.find((g) => g.goods_code === goodsCode)
    if (!item) throw new Error('货物不存在')
    const nodes = await getMockNodes()
    const node = nodes.find((n) => n.node_code === item.node_code)
    return {
      ...item,
      node_name: node?.name ?? item.node_code,
      updated_at: item.updated_at ?? item.created_at,
    }
  }
  const { data } = await request.get<GoodsDetail>(
    `/goods/${encodeURIComponent(goodsCode)}`,
  )
  return data
}
