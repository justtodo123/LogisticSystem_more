import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { Driver, DriverDetail } from '@/types/driver'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockDrivers, getMockNodes } from '@/utils/mock-store'

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

export async function getDriver(driverCode: string): Promise<DriverDetail> {
  if (useMockBasicData()) {
    const drivers = await getMockDrivers()
    const driver = drivers.find((d) => d.driver_code === driverCode)
    if (!driver) throw new Error('司机不存在')
    const nodes = await getMockNodes()
    const node = nodes.find((n) => n.node_code === driver.node_code)
    return {
      ...driver,
      node_name: node?.name ?? driver.node_code,
      updated_at: driver.updated_at ?? driver.created_at,
    }
  }
  const { data } = await request.get<DriverDetail>(
    `/drivers/${encodeURIComponent(driverCode)}`,
  )
  return data
}
