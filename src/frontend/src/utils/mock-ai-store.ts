import type {
  AiParseData,
  AiParseMode,
  AiParseRequest,
  AiParseResult,
  AlgorithmParams,
} from '@/types/ai'
import type {
  GlobalScheduleDetail,
  GlobalScheduleSummary,
} from '@/types/schedule'
import {
  createMockGlobalSchedule,
  getMockScheduleDetail,
  getMockSchedules,
  registerMockScheduleDetail,
} from '@/utils/mock-store'
import { nextCode } from '@/utils/mock'

const MOCK_DEGRADED_KEYWORD = '降级测试'

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function nowIso(): string {
  return new Date().toISOString().slice(0, 19)
}

function resolveMode(payload: AiParseRequest): AiParseMode {
  const hasMessage = Boolean(payload.message?.trim())
  const hasWeights = Boolean(payload.weights)
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
    node_dispatch: {
      algorithm: 'traditional',
      weights: { distance: 0.5, time: 0.3, package_count: 0.2 },
    },
    route_planning: {
      algorithm: 'traditional',
      max_iterations: 1000,
    },
  }

  if (mode === 'ai' && payload.message?.includes('距离')) {
    base.global_schedule!.weights = { distance: 0.7, time: 0.1, package_count: 0.2 }
    base.node_dispatch!.weights = { distance: 0.7, time: 0.1, package_count: 0.2 }
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
  if (payload.weights?.node_dispatch) {
    base.node_dispatch = {
      ...base.node_dispatch,
      ...payload.weights.node_dispatch,
      weights: {
        ...base.node_dispatch?.weights,
        ...payload.weights.node_dispatch.weights,
      },
    }
  }
  if (payload.weights?.route_planning) {
    base.route_planning = {
      ...base.route_planning,
      ...payload.weights.route_planning,
    }
  }

  return base
}

async function mockReplanSchedule(
  originalCode: string,
): Promise<{ schedule_code: string; replan_results: AiParseData['replan_results'] }> {
  const original = await getMockScheduleDetail(originalCode)
  if (!original) {
    throw new Error(`原调度方案不存在: ${originalCode}`)
  }

  const schedules = await getMockSchedules()
  const newScheduleCode = nextCode(
    'GS',
    schedules.map((s) => s.schedule_code),
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

  return {
    schedule_code: newScheduleCode,
    replan_results: [
      {
        original_schedule_code: originalCode,
        new_schedule_code: newScheduleCode,
      },
    ],
  }
}

export async function mockParseAi(payload: AiParseRequest): Promise<AiParseResult> {
  await delay(payload.execute === false ? 600 : 1200)

  const mode = resolveMode(payload)
  const algorithm_params = mergeAlgorithmParams(payload, mode)
  const isReplan = Boolean(payload.schedule_codes?.length)
  const degraded = Boolean(payload.message?.includes(MOCK_DEGRADED_KEYWORD))

  if (payload.execute === false) {
    return {
      data: {
        algorithm_params,
        mode,
        is_replan: isReplan,
        executed: false,
        reference_codes: payload.schedule_codes ?? null,
        schedule_code: null,
        replan_results: null,
      },
      meta: {
        degraded,
        degraded_reason: degraded
          ? 'Mock：DeepSeek API Key 未配置（演示降级）'
          : null,
      },
    }
  }

  if (isReplan && payload.schedule_codes) {
    const replanResults: NonNullable<AiParseData['replan_results']> = []
    let firstCode: string | null = null
    for (const code of payload.schedule_codes) {
      const result = await mockReplanSchedule(code)
      if (result.replan_results?.[0]) {
        replanResults.push(result.replan_results[0])
      }
      if (!firstCode) {
        firstCode = result.schedule_code
      }
    }

    return {
      data: {
        schedule_code: firstCode,
        replan_results: replanResults,
        algorithm_params,
        mode: mode,
        is_replan: true,
        executed: true,
        reference_codes: payload.schedule_codes,
      },
      meta: {
        degraded,
        degraded_reason: degraded
          ? 'Mock：DeepSeek API 调用超时（演示降级）'
          : null,
      },
    }
  }

  const summary = await createMockGlobalSchedule()
  return {
    data: {
      schedule_code: summary.schedule_code,
      replan_results: null,
      algorithm_params,
      mode,
      is_replan: false,
      executed: true,
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
