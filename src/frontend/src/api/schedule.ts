import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type {
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
  createMockGlobalSchedule,
  createMockNodeDispatch,
  getMockBatchDetail,
  getMockBatches,
  getMockScheduleDetail,
  getMockSchedules,
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
  await registerMockScheduleDetail(data)
}

export async function createGlobalSchedule(
  payload: GlobalScheduleCreatePayload = {},
): Promise<GlobalScheduleSummary> {
  if (useMockSchedule()) {
    if (payload.simulate_failure) {
      throw new Error('无法完成全局调度，请增加1级分拣中心容量或减少订单')
    }
    return createMockGlobalSchedule()
  }

  const { data } = await request.post<GlobalScheduleSummary>(
    '/schedule/global',
    {
      algorithm: payload.algorithm ?? 'traditional',
      ...(payload.order_codes?.length
        ? { order_codes: payload.order_codes }
        : {}),
    },
    { timeout: 30000 },
  )
  if (useMockNodeDispatch()) {
    try {
      await ensureScheduleCachedForMockDispatch(data.schedule_code)
    } catch {
      await registerMockScheduleDetail({
        ...data,
        goods_schedules: [],
        algorithm_type: 'traditional',
      })
    }
  }
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
  return data
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
  return data
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
