import request, { postWithMeta } from './request'
import { useMockAi } from '@/utils/env'
import { mockParseAi, mockP1NotImplemented } from '@/utils/mock-ai-store'
import type {
  AiAnalyzeExceptionRequest,
  AiExplainRequest,
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

export async function explainSchedule(payload: AiExplainRequest): Promise<void> {
  if (useMockAi()) {
    await mockP1NotImplemented('F015 方案解释')
    return
  }

  try {
    await request.post('/ai/explain', payload)
  } catch (err) {
    throw normalizeP1Error(err)
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
