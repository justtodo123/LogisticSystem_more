import type {
  AiParseData,
  AiParseMode,
  AiParseRequest,
  AiParseResult,
  AlgorithmParams,
} from '@/types/ai'
import type { GlobalScheduleDetail } from '@/types/schedule'
import {
  getMockScheduleDetail,
  getMockSchedules,
  previewMockSchedule,
} from '@/utils/mock-store'

const MOCK_DEGRADED_KEYWORD = '降级测试'

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function resolveMode(payload: AiParseRequest): AiParseMode {
  const hasMessage = Boolean(payload.message?.trim())
  const hasWeights = Boolean(payload.weights?.global_schedule)
  if (hasMessage && hasWeights) return 'hybrid'
  if (hasMessage) return 'ai'
  if (hasWeights) return 'manual'
  return 'default'
}

function mergeAlgorithmParams(
  payload: AiParseRequest,
  mode: AiParseMode,
): AlgorithmParams {
  const base: AlgorithmParams = {
    global_schedule: {
      algorithm: 'traditional',
      weights: { distance: 0.5, time: 0.3, package_count: 0.2 },
    },
  }

  if (mode === 'ai' && payload.message?.includes('距离')) {
    base.global_schedule!.weights = { distance: 0.7, time: 0.1, package_count: 0.2 }
  }

  if (payload.weights?.global_schedule) {
    base.global_schedule = {
      ...base.global_schedule,
      ...payload.weights.global_schedule,
      weights: {
        ...base.global_schedule?.weights,
        ...payload.weights.global_schedule.weights,
      },
    }
  }

  return base
}


async function mockReplanDraft(
  originalCode: string,
): Promise<{ schedule_code: string; replan_results: AiParseData['replan_results'] }> {
  const original = await getMockScheduleDetail(originalCode)
  if (!original) {
    throw new Error(`原调度方案不存在: ${originalCode}`)
  }

  const summary = await previewMockSchedule(original.order_codes, 'traditional', {
    isReplan: true,
    baseDetail: original as GlobalScheduleDetail,
  })

  return {
    schedule_code: summary.schedule_code,
    replan_results: [
      {
        original_schedule_code: originalCode,
        new_schedule_code: summary.schedule_code,
      },
    ],
  }
}

export async function mockParseAi(payload: AiParseRequest): Promise<AiParseResult> {
  const execute = payload.execute ?? 'draft'
  await delay(execute === 'dry-run' ? 600 : 1200)

  const mode = resolveMode(payload)
  const algorithm_params = mergeAlgorithmParams(payload, mode)
  const isReplan = Boolean(payload.schedule_codes?.length)
  const degraded = Boolean(payload.message?.includes(MOCK_DEGRADED_KEYWORD))

  if (execute === 'dry-run') {
    return {
      data: {
        algorithm_params,
        mode,
      },
      meta: {
        degraded,
        degraded_reason: degraded
          ? 'Mock：DeepSeek API Key 未配置（演示降级）'
          : null,
      },
    }
  }

  if (isReplan && payload.schedule_codes?.length) {
    const firstCode = payload.schedule_codes[0]
    const result = await mockReplanDraft(firstCode)
    const multiNote =
      payload.schedule_codes.length > 1
        ? '（Mock：后端仅处理首个方案）'
        : ''

    return {
      data: {
        schedule_code: result.schedule_code,
        replan_results: result.replan_results,
        algorithm_params,
        mode,
        is_replan: true,
        status: 'draft',
        reference_codes: payload.schedule_codes,
      },
      meta: {
        degraded,
        degraded_reason: degraded
          ? `Mock：DeepSeek API 调用超时（演示降级）${multiNote}`
          : multiNote || null,
      },
    }
  }

  const summary = await previewMockSchedule()
  await getMockSchedules()

  return {
    data: {
      schedule_code: summary.schedule_code,
      replan_results: null,
      algorithm_params,
      mode,
      is_replan: false,
      status: 'draft',
      reference_codes: null,
    },
    meta: {
      degraded,
      degraded_reason: degraded
        ? 'Mock：DeepSeek 返回格式错误，已使用默认参数'
        : null,
    },
  }
}

export async function mockP1NotImplemented(feature: string): Promise<void> {
  await delay(300)
  throw new Error(`${feature}功能正在开发中（P1）`)
}
