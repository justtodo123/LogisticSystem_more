import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { Driver } from '@/types/driver'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockDrivers } from '@/utils/mock-store'

export async function listDrivers(
  params: ApiListParams = {},
): Promise<PaginatedResult<Driver>> {
  if (useMockBasicData()) {
    const drivers = await getMockDrivers()
    return filterAndPaginate(drivers, params, (item, p) => {
      if (p.status && item.status !== p.status) return false
      if (p.node_code && item.node_code !== p.node_code) return false
      return true
    })
  }
  const { data } = await request.get<PaginatedResult<Driver>>('/drivers', {
    params,
  })
  return data
}
