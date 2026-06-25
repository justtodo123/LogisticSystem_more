import type {
  DispatchBatchDetail,
  DispatchBatchSummary,
  DispatchTask,
  NodeDispatchItem,
  NodeDispatchPhase,
  NodeDispatchResult,
} from '@/types/dispatch'

function normalizeDispatchTask(task: DispatchTask): DispatchTask {
  return {
    ...task,
    package_codes:
      task.package_codes ??
      task.package_details?.map((p) => p.package_code) ??
      [],
  }
}

function normalizeDispatchItem(item: NodeDispatchItem): NodeDispatchItem {
  return {
    ...item,
    tasks: item.tasks.map(normalizeDispatchTask),
  }
}

function isMockPhase(
  item: NodeDispatchPhase | NodeDispatchItem,
): item is NodeDispatchPhase {
  return 'vehicle_tasks' in item
}

/** Mock 分组结构 → 与 API 一致的扁平调度明细 */
export function flattenDispatches(
  dispatches: Array<NodeDispatchPhase | NodeDispatchItem>,
): NodeDispatchItem[] {
  if (!dispatches.length) return []
  if (!isMockPhase(dispatches[0])) {
    return (dispatches as NodeDispatchItem[]).map(normalizeDispatchItem)
  }
  return (dispatches as NodeDispatchPhase[]).flatMap((phase) =>
    phase.vehicle_tasks.map((vt) =>
      normalizeDispatchItem({
        dispatch_code: phase.dispatch_code,
        vehicle_code: vt.vehicle_code,
        driver_code: vt.driver_code,
        level_phase: phase.level_phase,
        tasks: vt.tasks,
        total_distance: vt.distance,
      }),
    ),
  )
}

export function normalizeBatchSummary(
  raw: DispatchBatchSummary & {
    l0_l1_dispatch_count?: number
    l1_l2_dispatch_count?: number
  },
): DispatchBatchSummary {
  const l0 = raw.l0_l1_dispatch_count ?? 0
  const l1 = raw.l1_l2_dispatch_count ?? 0
  return {
    ...raw,
    vehicle_count: raw.vehicle_count ?? l0 + l1,
  }
}

export function normalizeBatchDetail(
  raw: Omit<DispatchBatchDetail, 'vehicle_count' | 'dispatches'> & {
    dispatches?: Array<NodeDispatchPhase | NodeDispatchItem>
    l0_l1_dispatch_count?: number
    l1_l2_dispatch_count?: number
    vehicle_count?: number
  },
): DispatchBatchDetail {
  const dispatches = flattenDispatches(raw.dispatches ?? [])
  const l0 =
    raw.l0_l1_dispatch_count ??
    dispatches.filter((d) => d.level_phase === 0).length
  const l1 =
    raw.l1_l2_dispatch_count ??
    dispatches.filter((d) => d.level_phase === 1).length
  return {
    ...raw,
    l0_l1_dispatch_count: l0,
    l1_l2_dispatch_count: l1,
    vehicle_count: raw.vehicle_count ?? l0 + l1,
    dispatches,
  }
}

export function normalizeNodeDispatchResult(
  raw: {
    batch_code: string
    status: NodeDispatchResult['status']
    dispatches?: NodeDispatchItem[]
    l0_l1_dispatch_count?: number
    l1_l2_dispatch_count?: number
    route_codes?: string[]
  },
): NodeDispatchResult {
  const dispatches = raw.dispatches ?? []
  const l0 =
    raw.l0_l1_dispatch_count ??
    dispatches.filter((d) => d.level_phase === 0).length
  const l1 =
    raw.l1_l2_dispatch_count ??
    dispatches.filter((d) => d.level_phase === 1).length
  return {
    batch_code: raw.batch_code,
    status: raw.status,
    l0_l1_dispatch_count: l0,
    l1_l2_dispatch_count: l1,
    route_codes: raw.route_codes,
  }
}
