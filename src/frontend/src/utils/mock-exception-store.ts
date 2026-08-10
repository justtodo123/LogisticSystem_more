import type { PaginatedResult } from '@/types/common'
import type {
  BatchReplanPayload,
  BatchReplanResult,
  CreateExceptionPayload,
  ExceptionEvent,
  ExceptionListParams,
  RedispatchReplanResult,
  ReplanStrategy,
  RerouteReplanResult,
} from '@/types/exception'
import type { GlobalScheduleDetail, GlobalScheduleSummary } from '@/types/schedule'
import type { RouteListItem } from '@/types/route'
import type { ApiListParams } from '@/types/common'
import {
  getMockBatchDetail,
  getMockBatches,
  getMockScheduleDetail,
  getMockSchedules,
  registerMockScheduleDetail,
} from '@/utils/mock-store'
import { filterAndPaginate, nextCode } from '@/utils/mock'

let exceptionsData: ExceptionEvent[] = []
let mockRoutesData: RouteListItem[] = []

function nowIso(): string {
  return new Date().toISOString().slice(0, 19)
}

function nextEventCode(): string {
  const ts = Date.now()
  const existing = exceptionsData.map((e) => e.event_code)
  let code = `EX${ts}`
  while (existing.includes(code)) {
    code = `EX${ts}${Math.floor(Math.random() * 10)}`
  }
  return code
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function listMockExceptions(
  params: ExceptionListParams,
): Promise<PaginatedResult<ExceptionEvent>> {
  return filterAndPaginate(exceptionsData, params, (item, p) => {
    const status = p.status as string | undefined
    const type = p.exception_type as string | undefined
    if (status && item.status !== status) return false
    if (type && item.exception_type !== type) return false
    return true
  })
}

export async function getMockException(
  eventCode: string,
): Promise<ExceptionEvent | null> {
  return exceptionsData.find((e) => e.event_code === eventCode) ?? null
}

export async function createMockException(
  payload: CreateExceptionPayload,
): Promise<ExceptionEvent> {
  if (payload.recommended_action === 'reroute') {
    if (payload.target_type !== 'route' || !payload.target_code) {
      throw new Error('reroute 操作要求 target_type=route 且填写路线编号')
    }
  }

  if (payload.related_schedule_code) {
    const schedule = await getMockScheduleDetail(payload.related_schedule_code)
    if (!schedule) {
      throw new Error('关联调度方案不存在')
    }
  }

  await delay(400)

  const event: ExceptionEvent = {
    event_code: nextEventCode(),
    exception_type: payload.exception_type,
    exception_subtype: payload.exception_subtype ?? null,
    target_type: payload.target_type ?? null,
    target_code: payload.target_code ?? null,
    recommended_action: payload.recommended_action,
    related_schedule_code: payload.related_schedule_code ?? null,
    replan_batch_code: null,
    description: payload.description,
    status: 'open',
    resolved_at: null,
    created_at: nowIso(),
  }

  exceptionsData = [event, ...exceptionsData]
  return event
}

async function findBatchForSchedule(scheduleCode: string): Promise<string | null> {
  const batches = await getMockBatches()
  const match = batches.find((b) => b.schedule_code === scheduleCode)
  return match?.batch_code ?? null
}

export async function mockRedispatchReplan(
  eventCode: string,
  reason: string,
  strategy: ReplanStrategy = 'full',
): Promise<RedispatchReplanResult> {
  const event = await getMockException(eventCode)
  if (!event) throw new Error('异常事件不存在')
  if (event.status === 'resolved') {
    throw new Error('异常已解决，无法重规划')
  }
  if (!event.related_schedule_code) {
    throw new Error('redispatch 缺少 related_schedule_code')
  }

  const original = await getMockScheduleDetail(event.related_schedule_code)
  if (!original) {
    throw new Error('关联调度方案不存在')
  }

  await delay(1500)

  const schedules = await getMockSchedules()
  const newScheduleCode = nextCode(
    'GS',
    schedules.map((s) => s.schedule_code),
  )
  const batches = await getMockBatches()
  const newBatchCode = nextCode(
    'DB',
    batches.map((b) => b.batch_code),
  )
  const newVersion = (original.version ?? 1) + 1
  const createdAt = nowIso()

  const summary: GlobalScheduleSummary = {
    schedule_code: newScheduleCode,
    total_distance: original.total_distance,
    total_time: original.total_time,
    total_goods: original.total_goods,
    score: original.score,
    package_count: original.package_count,
    version: newVersion,
    is_replan: true,
    created_at: createdAt,
  }

  const detail: GlobalScheduleDetail = {
    ...summary,
    algorithm_type: original.algorithm_type ?? 'traditional',
    order_codes: original.order_codes,
    goods_schedules: original.goods_schedules,
  }

  await registerMockScheduleDetail(detail)

  event.replan_batch_code = newBatchCode
  const idx = exceptionsData.findIndex((e) => e.event_code === eventCode)
  if (idx >= 0) {
    exceptionsData[idx] = { ...event }
  }

  return {
    schedule_code: newScheduleCode,
    new_schedule_code: newScheduleCode,
    batch_code: newBatchCode,
    version: newVersion,
    is_replan: true,
    replan_reason: reason,
    original_schedule_code: original.schedule_code,
    strategy,
    diff_summary: {
      strategy,
      affected_count: strategy === 'partial' ? 1 : (original.package_count ?? 0),
      new_eta_delta: 0.0,
      cost_delta: 0.0,
    },
  }
}

export async function mockRerouteReplan(
  eventCode: string,
  reason: string,
): Promise<RerouteReplanResult> {
  const event = await getMockException(eventCode)
  if (!event) throw new Error('异常事件不存在')
  if (event.status === 'resolved') {
    throw new Error('异常已解决，无法重规划')
  }
  if (!event.target_code) {
    throw new Error('reroute 缺少 target_code')
  }

  const originalRouteCode = event.target_code
  const routeEntry = mockRoutesData.find(
    (r) => r.route_code === originalRouteCode,
  )
  const batchCode =
    routeEntry?.batch_code ??
    (event.related_schedule_code
      ? await findBatchForSchedule(event.related_schedule_code)
      : null)

  if (!batchCode) {
    throw new Error('未找到关联批次，请先完成节点间调度')
  }

  await delay(1200)

  const newRouteCode = nextCode(
    'RT',
    mockRoutesData.map((r) => r.route_code),
  )
  const newVersion = 2

  mockRoutesData = [
    {
      route_code: newRouteCode,
      batch_code: batchCode,
      vehicle_code: routeEntry?.vehicle_code,
      total_distance: routeEntry?.total_distance,
    },
    ...mockRoutesData,
  ]

  event.replan_batch_code = batchCode
  const idx = exceptionsData.findIndex((e) => e.event_code === eventCode)
  if (idx >= 0) {
    exceptionsData[idx] = { ...event }
  }

  return {
    batch_code: batchCode,
    route_codes: [newRouteCode],
    new_route_code: newRouteCode,
    version: newVersion,
    is_replan: true,
    replan_reason: reason,
    original_route_code: originalRouteCode,
  }
}

export async function resolveMockException(
  eventCode: string,
): Promise<ExceptionEvent> {
  const event = await getMockException(eventCode)
  if (!event) throw new Error('异常事件不存在')
  if (event.status === 'resolved') {
    throw new Error('异常已解决，重复标记拒绝')
  }

  const updated: ExceptionEvent = {
    ...event,
    status: 'resolved',
    resolved_at: nowIso(),
  }
  const idx = exceptionsData.findIndex((e) => e.event_code === eventCode)
  if (idx >= 0) {
    exceptionsData[idx] = updated
  }
  return updated
}

export async function mockBatchReplan(
  payload: BatchReplanPayload,
): Promise<BatchReplanResult> {
  const { event_codes, reason, strategy = 'full' } = payload
  await delay(400)

  // 按关联调度方案分组（同一方案只重规划一次）
  const scheduleToEvents = new Map<string, ExceptionEvent[]>()
  const skipped: string[] = []
  for (const code of event_codes) {
    const ev = await getMockException(code)
    if (!ev || ev.status === 'resolved' || !ev.related_schedule_code) {
      skipped.push(code)
      continue
    }
    const list = scheduleToEvents.get(ev.related_schedule_code) ?? []
    list.push(ev)
    scheduleToEvents.set(ev.related_schedule_code, list)
  }

  const replannedSchedules = []
  for (const [scheduleCode, evts] of scheduleToEvents) {
    const first = evts[0]
    let newCode: string | null = null
    let replanStrategy: ReplanStrategy = strategy
    let diff = null
    try {
      const result = await mockRedispatchReplan(first.event_code, reason, strategy)
      newCode = result.new_schedule_code
      replanStrategy = result.strategy ?? strategy
      diff = result.diff_summary ?? null
      for (const ev of evts) {
        ev.replan_batch_code = newCode
        const idx = exceptionsData.findIndex((e) => e.event_code === ev.event_code)
        if (idx >= 0) exceptionsData[idx] = { ...ev }
      }
    } catch {
      newCode = null
    }
    replannedSchedules.push({
      schedule_code: scheduleCode,
      event_codes: evts.map((e) => e.event_code),
      result_code: newCode ? 0 : 40001,
      message: newCode ? 'success' : '重规划失败',
      new_schedule_code: newCode,
      strategy: replanStrategy,
      diff_summary: diff,
    })
  }

  return {
    replanned_schedules: replannedSchedules,
    skipped,
    total_events: event_codes.length,
    strategy,
  }
}

export async function listMockRoutes(
  params: ApiListParams & { batch_code?: string; vehicle_code?: string },
): Promise<PaginatedResult<RouteListItem>> {
  if (mockRoutesData.length === 0) {
    const batches = await getMockBatches()
    const items: RouteListItem[] = []
    for (const batch of batches) {
      const detail = await getMockBatchDetail(batch.batch_code)
      const codes = detail?.route_codes ?? []
      for (const code of codes) {
        items.push({
          route_code: code,
          batch_code: batch.batch_code,
        })
      }
      if (detail?.dispatches?.length) {
        for (const d of detail.dispatches) {
          if (codes.length) continue
          items.push({
            route_code: `RT${batch.batch_code.slice(2)}${d.vehicle_code.slice(-2)}`,
            batch_code: batch.batch_code,
            vehicle_code: d.vehicle_code,
          })
        }
      }
    }
    mockRoutesData = items
  }

  return filterAndPaginate(mockRoutesData, params, (item, p) => {
    const batchCode = p.batch_code as string | undefined
    const vehicleCode = p.vehicle_code as string | undefined
    if (batchCode && item.batch_code !== batchCode) return false
    if (vehicleCode && item.vehicle_code !== vehicleCode) return false
    return true
  })
}

export function resetMockExceptionStore(): void {
  exceptionsData = []
  mockRoutesData = []
}
