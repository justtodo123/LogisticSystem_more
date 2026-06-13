import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type {
  GlobalScheduleCreatePayload,
  GlobalScheduleDetail,
  GlobalScheduleSummary,
} from '@/types/schedule'
import { useMockSchedule } from '@/utils/env'
import { filterAndPaginate } from '@/utils/mock'
import {
  createMockGlobalSchedule,
  getMockScheduleDetail,
  getMockSchedules,
} from '@/utils/mock-store'

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
