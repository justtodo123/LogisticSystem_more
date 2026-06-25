import request, { postWithBusinessCode, postWithMeta } from './request'
import { useMockAi } from '@/utils/env'
import { mockExplainSchedule, mockParseAi, mockP1NotImplemented } from '@/utils/mock-ai-store'
import type {
  AiAnalyzeExceptionRequest,
  AiExplainData,
  AiExplainRawData,
  AiExplainRequest,
  AiExplainResult,
  AiParseData,
  AiParseRequest,
  AiParseResult,
  AiReviewRequest,
} from '@/types/ai'

export async function parseAi(payload: AiParseRequest): Promise<AiParseResult> {
  if (useMockAi()) {
    return mockParseAi(payload)
  }

  const { data, meta } = await postWithMeta<AiParseData>('/ai/parse', payload, {
    timeout: 60000,
  })
  return { data, meta }
}

function normalizeExplainData(raw: AiExplainRawData, scheduleCode: string): AiExplainData {
  return {
    schedule_code: scheduleCode,
    explanation: raw.explanation,
    sections: {
      key_decisions: raw.key_decisions?.length ? raw.key_decisions : undefined,
      risks: raw.potential_risks?.length ? raw.potential_risks : undefined,
      suggestions: raw.suggestions?.length ? raw.suggestions : undefined,
    },
  }
}

export async function explainSchedule(payload: AiExplainRequest): Promise<AiExplainResult> {
  if (useMockAi()) {
    return mockExplainSchedule(payload)
  }

  const result = await postWithBusinessCode<AiExplainRawData>(
    '/ai/explain',
    { schedule_code: payload.schedule_code },
    { timeout: 70000 },
  )
  return {
    data: result.data
      ? normalizeExplainData(result.data, payload.schedule_code)
      : null,
    meta: result.meta,
    pending: result.pending,
    message: result.message,
  }
}

export async function reviewSchedule(payload: AiReviewRequest): Promise<void> {
  if (useMockAi()) {
    await mockP1NotImplemented('F016 方案审查')
    return
  }

  try {
    await request.post('/ai/review', payload)
  } catch (err) {
    throw normalizeP1Error(err)
  }
}

export async function analyzeException(
  payload: AiAnalyzeExceptionRequest,
): Promise<void> {
  if (useMockAi()) {
    await mockP1NotImplemented('F017 异常分析')
    return
  }

  try {
    await request.post('/ai/analyze-exception', payload)
  } catch (err) {
    throw normalizeP1Error(err)
  }
}

function normalizeP1Error(err: unknown): Error {
  if (err instanceof Error && err.message.includes('501')) {
    return new Error(err.message)
  }
  return err instanceof Error ? err : new Error('请求失败')
}
