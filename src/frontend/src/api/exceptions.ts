import request from './request'
import type { PaginatedResult } from '@/types/common'
import type {
  CreateExceptionPayload,
  ExceptionEvent,
  ExceptionListParams,
  ReplanResult,
  TriggerReplanPayload,
} from '@/types/exception'
import { useMockExceptions } from '@/utils/env'
import {
  createMockException,
  getMockException,
  listMockExceptions,
  mockRedispatchReplan,
  mockRerouteReplan,
  resolveMockException,
} from '@/utils/mock-exception-store'

export async function listExceptions(
  params: ExceptionListParams = {},
): Promise<PaginatedResult<ExceptionEvent>> {
  if (useMockExceptions()) {
    return listMockExceptions(params)
  }

  const query: Record<string, string | number> = {
    page: params.page ?? 1,
    page_size: params.page_size ?? 20,
  }
  if (params.status) query.status = params.status
  if (params.exception_type) query.exception_type = params.exception_type

  const { data } = await request.get<PaginatedResult<ExceptionEvent>>(
    '/exceptions',
    { params: query },
  )
  return data
}

export async function createException(
  payload: CreateExceptionPayload,
): Promise<ExceptionEvent> {
  if (useMockExceptions()) {
    return createMockException(payload)
  }

  const { data } = await request.post<ExceptionEvent>('/exceptions', payload)
  return data
}

export async function getException(eventCode: string): Promise<ExceptionEvent> {
  if (useMockExceptions()) {
    const event = await getMockException(eventCode)
    if (!event) {
      throw new Error('异常事件不存在')
    }
    return event
  }

  const { data } = await request.get<ExceptionEvent>(
    `/exceptions/${encodeURIComponent(eventCode)}`,
  )
  return data
}

export async function triggerReplan(
  eventCode: string,
  payload: TriggerReplanPayload,
): Promise<ReplanResult> {
  if (useMockExceptions()) {
    if (payload.action === 'redispatch') {
      return mockRedispatchReplan(eventCode, payload.reason)
    }
    return mockRerouteReplan(eventCode, payload.reason)
  }

  const { data } = await request.post<ReplanResult>(
    `/exceptions/${encodeURIComponent(eventCode)}/replan`,
    payload,
    { timeout: 60000 },
  )
  return data
}

export async function resolveException(
  eventCode: string,
): Promise<ExceptionEvent> {
  if (useMockExceptions()) {
    return resolveMockException(eventCode)
  }

  const { data } = await request.put<ExceptionEvent>(
    `/exceptions/${encodeURIComponent(eventCode)}/resolve`,
  )
  return data
}
