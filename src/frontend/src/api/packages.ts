import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { PackageItem } from '@/types/package'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockPackages } from '@/utils/mock-store'

export async function listPackages(
  params: ApiListParams = {},
): Promise<PaginatedResult<PackageItem>> {
  if (useMockBasicData()) {
    const packages = await getMockPackages()
    return filterAndPaginate(packages, params, (item, p) => {
      if (p.status && item.status !== p.status) return false
      if (p.from_node_code && item.from_node_code !== p.from_node_code) {
        return false
      }
      if (p.to_node_code && item.to_node_code !== p.to_node_code) return false
      return true
    })
  }
  const { data } = await request.get<PaginatedResult<PackageItem>>(
    '/packages',
    { params },
  )
  return data
}
