import type {
  GlobalScheduleDetail,
  GlobalScheduleSummary,
  GoodsScheduleItem,
} from '@/types/schedule'

interface PathNodeRaw {
  node_code: string
  node_name?: string
}

function isPathNodeArray(
  path: unknown,
): path is PathNodeRaw[] {
  return (
    Array.isArray(path) &&
    path.length > 0 &&
    typeof path[0] === 'object' &&
    path[0] != null &&
    'node_code' in path[0]
  )
}

export function normalizeGoodsScheduleItem(
  raw: GoodsScheduleItem & { path?: string[] | PathNodeRaw[] },
): GoodsScheduleItem {
  const path = raw.path ?? []
  if (isPathNodeArray(path)) {
    const nodes = path as PathNodeRaw[]
    return {
      ...raw,
      path: nodes.map((p) => p.node_code),
      path_labels: nodes.map((p) => p.node_name ?? p.node_code),
    }
  }
  return raw as GoodsScheduleItem
}

export function normalizeGlobalScheduleDetail(
  data: GlobalScheduleDetail & {
    goods_schedules?: Array<
      GoodsScheduleItem & { path?: string[] | PathNodeRaw[] }
    >
  },
): GlobalScheduleDetail {
  return {
    ...data,
    goods_schedules: (data.goods_schedules ?? []).map(normalizeGoodsScheduleItem),
  }
}

export function normalizeGlobalScheduleSummary(
  data: GlobalScheduleSummary,
): GlobalScheduleSummary {
  return data
}
