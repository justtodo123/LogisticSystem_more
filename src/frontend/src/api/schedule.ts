import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type {
  DiscardDraftResult,
  GlobalScheduleCreatePayload,
  GlobalScheduleDetail,
  GlobalScheduleSummary,
} from '@/types/schedule'
import type {
  DispatchBatchDetail,
  DispatchBatchSummary,
  NodeDispatchCreatePayload,
  NodeDispatchResult,
} from '@/types/dispatch'
import { useMockSchedule, useMockNodeDispatch } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import {
  normalizeBatchDetail,
  normalizeBatchSummary,
  normalizeNodeDispatchResult,
} from '@/utils/dispatch-normalize'
import {
  normalizeGlobalScheduleDetail,
  normalizeGlobalScheduleSummary,
} from '@/utils/schedule-normalize'
import {
  confirmMockSchedule,
  createMockNodeDispatch,
  discardMockSchedule,
  getMockBatchDetail,
  getMockBatches,
  getMockScheduleDetail,
  getMockSchedules,
  previewMockSchedule,
  registerMockScheduleDetail,
} from '@/utils/mock-store'

/** 节点间调度 Mock 需要方案详情；全局调度走真实 API 时从后端拉取并缓存 */
async function ensureScheduleCachedForMockDispatch(
  scheduleCode: string,
): Promise<void> {
  if (await getMockScheduleDetail(scheduleCode)) {
    return
  }
  const { data } = await request.get<GlobalScheduleDetail>(
    `/schedule/global/${scheduleCode}`,
  )
  const normalized = normalizeGlobalScheduleDetail(data)
  await registerMockScheduleDetail(normalized)
}

export async function previewGlobalSchedule(
  payload: GlobalScheduleCreatePayload,
): Promise<GlobalScheduleSummary> {
  if (useMockSchedule()) {
    if (payload.simulate_failure) {
      throw new Error('无法完成全局调度，请增加1级分拣中心容量或减少订单')
    }
    return previewMockSchedule(payload.order_codes, payload.algorithm)
  }

  const { data } = await request.post<GlobalScheduleSummary>(
    '/schedule/global',
    {
      algorithm: payload.algorithm,
      preview: true,
      ...(payload.order_codes?.length
        ? { order_codes: payload.order_codes }
        : {}),
    },
    { timeout: 30000 },
  )
  return normalizeGlobalScheduleSummary(data)
}

export async function confirmGlobalSchedule(
  scheduleCode: string,
): Promise<GlobalScheduleSummary> {
  if (useMockSchedule()) {
    const confirmed = await confirmMockSchedule(scheduleCode)
    if (useMockNodeDispatch()) {
      const detail = await getMockScheduleDetail(scheduleCode)
      if (detail) {
        await registerMockScheduleDetail(detail)
      }
    }
    return confirmed
  }

  const { data } = await request.post<GlobalScheduleSummary>(
    `/schedule/confirm/${scheduleCode}`,
    undefined,
    { timeout: 30000 },
  )
  const normalized = normalizeGlobalScheduleSummary(data)
  if (useMockNodeDispatch()) {
    try {
      await ensureScheduleCachedForMockDispatch(scheduleCode)
    } catch {
      const detail = await getGlobalSchedule(scheduleCode)
      await registerMockScheduleDetail(detail)
    }
  }
  return normalized
}

export async function discardDraftSchedule(
  scheduleCode: string,
): Promise<DiscardDraftResult> {
  if (useMockSchedule()) {
    return discardMockSchedule(scheduleCode)
  }

  const { data } = await request.delete<DiscardDraftResult>(
    `/schedule/draft/${scheduleCode}`,
  )
  return data
}

export async function listGlobalSchedules(
  params: ApiListParams = {},
): Promise<PaginatedResult<GlobalScheduleSummary>> {
  if (useMockSchedule()) {
    const schedules = await getMockSchedules()
    return filterAndPaginate(schedules, params)
  }

  const { data } = await request.get<PaginatedResult<GlobalScheduleSummary>>(
    '/schedule/global',
    { params },
  )
  return {
    ...data,
    items: data.items.map(normalizeGlobalScheduleSummary),
  }
}

export async function getGlobalSchedule(
  scheduleCode: string,
): Promise<GlobalScheduleDetail> {
  if (useMockSchedule()) {
    const detail = await getMockScheduleDetail(scheduleCode)
    if (!detail) {
      throw new Error('调度方案不存在')
    }
    return detail
  }

  const { data } = await request.get<GlobalScheduleDetail>(
    `/schedule/global/${scheduleCode}`,
  )
  return normalizeGlobalScheduleDetail(data)
}

export async function createNodeDispatch(
  payload: NodeDispatchCreatePayload,
): Promise<NodeDispatchResult> {
  if (useMockNodeDispatch()) {
    if (!useMockSchedule()) {
      await ensureScheduleCachedForMockDispatch(payload.schedule_code)
    }
    return createMockNodeDispatch(payload)
  }

  const { data } = await request.post<NodeDispatchResult>(
    '/schedule/node-dispatch',
    {
      schedule_code: payload.schedule_code,
      demo_mode: payload.demo_mode ?? false,
    },
    { timeout: 30000 },
  )
  return normalizeNodeDispatchResult(data)
}

export async function listDispatchBatches(
  params: ApiListParams = {},
): Promise<PaginatedResult<DispatchBatchSummary>> {
  if (useMockNodeDispatch()) {
    const batches = await getMockBatches()
    const result = filterAndPaginate(batches, params, (item, p) => {
      const code = p.schedule_code as string | undefined
      if (code && item.schedule_code !== code) return false
      return true
    })
    return {
      ...result,
      items: result.items.map((item) => normalizeBatchSummary(item)),
    }
  }

  const { data } = await request.get<PaginatedResult<DispatchBatchSummary>>(
    '/schedule/batches',
    { params },
  )
  return {
    ...data,
    items: data.items.map((item) => normalizeBatchSummary(item)),
  }
}

export async function getDispatchBatch(
  batchCode: string,
): Promise<DispatchBatchDetail> {
  if (useMockNodeDispatch()) {
    const detail = await getMockBatchDetail(batchCode)
    if (!detail) {
      throw new Error('调度批次不存在')
    }
    return normalizeBatchDetail(detail)
  }

  const { data } = await request.get<DispatchBatchDetail>(
    `/schedule/batches/${batchCode}`,
  )
  return normalizeBatchDetail(data)
}
