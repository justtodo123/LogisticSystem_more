import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { Goods } from '@/types/goods'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockGoods } from '@/utils/mock-store'

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
