import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type {
  NodeDetail,
  NodeItem,
  NodeType,
  SortingCenterPayload,
  StorageCenterPayload,
} from '@/types/node'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import { getMockNodes } from '@/utils/mock-store'

function matchNodeType(item: NodeItem, nodeType?: string): boolean {
  if (!nodeType) return true
  return item.node_type === nodeType
}

export async function listNodes(
  params: ApiListParams = {},
): Promise<PaginatedResult<NodeItem>> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    return filterAndPaginate(nodes, params, (item, p) => {
      if (!matchNodeType(item, p.node_type as string | undefined)) return false
      if (p.level !== undefined && p.level !== '' && item.level !== Number(p.level)) {
        return false
      }
      return true
    })
  }
  const { data } = await request.get<PaginatedResult<NodeItem>>('/nodes', {
    params,
  })
  return data
}

export async function getNode(nodeCode: string): Promise<NodeDetail> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const node = nodes.find((n) => n.node_code === nodeCode)
    if (!node) throw new Error('节点不存在')
    return { ...node }
  }
  const { data } = await request.get<NodeDetail>(
    `/nodes/${encodeURIComponent(nodeCode)}`,
  )
  return data
}

export async function createStorageCenter(
  payload: StorageCenterPayload,
): Promise<NodeItem> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const item: NodeItem = {
      ...payload,
      node_type: 'storage_center',
      inventory: payload.inventory ?? 0,
      created_at: new Date().toISOString(),
    }
    nodes.unshift(item)
    return item
  }
  const { data } = await request.post<NodeItem>(
    '/nodes/storage-centers',
    payload,
  )
  return data
}

export async function updateStorageCenter(
  nodeCode: string,
  payload: Partial<StorageCenterPayload>,
): Promise<NodeItem> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const idx = nodes.findIndex((n) => n.node_code === nodeCode)
    if (idx < 0) throw new Error('节点不存在')
    nodes[idx] = { ...nodes[idx], ...payload }
    return nodes[idx]
  }
  const { data } = await request.put<NodeItem>(
    `/nodes/storage-centers/${nodeCode}`,
    payload,
  )
  return data
}

export async function deleteStorageCenter(nodeCode: string): Promise<void> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const idx = nodes.findIndex((n) => n.node_code === nodeCode)
    if (idx < 0) throw new Error('节点不存在')
    nodes.splice(idx, 1)
    return
  }
  await request.delete(`/nodes/storage-centers/${nodeCode}`)
}

export async function createSortingCenter(
  payload: SortingCenterPayload,
): Promise<NodeItem> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const item: NodeItem = {
      ...payload,
      node_type: 'sorting_center',
      created_at: new Date().toISOString(),
    }
    nodes.unshift(item)
    return item
  }
  const { data } = await request.post<NodeItem>(
    '/nodes/sorting-centers',
    payload,
  )
  return data
}

export async function updateSortingCenter(
  nodeCode: string,
  payload: Partial<SortingCenterPayload>,
): Promise<NodeItem> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const idx = nodes.findIndex((n) => n.node_code === nodeCode)
    if (idx < 0) throw new Error('节点不存在')
    nodes[idx] = { ...nodes[idx], ...payload }
    return nodes[idx]
  }
  const { data } = await request.put<NodeItem>(
    `/nodes/sorting-centers/${nodeCode}`,
    payload,
  )
  return data
}

export async function deleteSortingCenter(nodeCode: string): Promise<void> {
  if (useMockBasicData()) {
    const nodes = await getMockNodes()
    const idx = nodes.findIndex((n) => n.node_code === nodeCode)
    if (idx < 0) throw new Error('节点不存在')
    nodes.splice(idx, 1)
    return
  }
  await request.delete(`/nodes/sorting-centers/${nodeCode}`)
}

function isLevel0SortingCenter(node: NodeItem): boolean {
  if (node.level === 0) return true
  if (node.level === 1) return false
  // 后端列表可能未返回 level，按 seed 编号约定：L2*=0级，L1*=1级
  if (node.node_code.startsWith('L2')) return true
  if (node.node_code.startsWith('L1')) return false
  return node.level === 0
}

export async function listLevel0SortingCenters(): Promise<NodeItem[]> {
  const result = await listNodes({
    node_type: 'sorting_center',
    page: 1,
    page_size: 200,
  })
  return result.items.filter(isLevel0SortingCenter)
}

function isLevel1SortingCenter(node: NodeItem): boolean {
  if (node.level === 1) return true
  if (node.level === 0) return false
  if (node.node_code.startsWith('L1')) return true
  if (node.node_code.startsWith('L2')) return false
  if (node.node_code.startsWith('SO10')) return true
  return node.level === 1
}

export async function listLevel1SortingCenters(): Promise<NodeItem[]> {
  const result = await listNodes({
    node_type: 'sorting_center',
    page: 1,
    page_size: 200,
  })
  return result.items.filter(isLevel1SortingCenter)
}

export function nodeTypeLabel(type: NodeType): string {
  return type === 'storage_center' ? '存储中心' : '分拣中心'
}
