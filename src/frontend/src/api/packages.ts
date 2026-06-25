import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { PackageDetail, PackageItem } from '@/types/package'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockNodes, getMockPackages } from '@/utils/mock-store'

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

async function enrichPackageDetail(pkg: PackageItem): Promise<PackageDetail> {
  const nodes = await getMockNodes()
  const from = nodes.find((n) => n.node_code === pkg.from_node_code)
  const to = nodes.find((n) => n.node_code === pkg.to_node_code)
  return {
    ...pkg,
    from_node_name: from?.name ?? pkg.from_node_code,
    to_node_name: to?.name ?? pkg.to_node_code,
    updated_at: pkg.updated_at ?? pkg.created_at,
  }
}

export async function getPackage(packageCode: string): Promise<PackageDetail> {
  if (useMockBasicData()) {
    const packages = await getMockPackages()
    const pkg = packages.find((p) => p.package_code === packageCode)
    if (!pkg) throw new Error('包裹不存在')
    return enrichPackageDetail(pkg)
  }
  const { data } = await request.get<PackageDetail>(
    `/packages/${encodeURIComponent(packageCode)}`,
  )
  return data
}
