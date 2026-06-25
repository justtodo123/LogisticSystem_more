import type {
  AiExplainData,
  AiExplainRequest,
  AiExplainResult,
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

function formatScoreLine(detail: GlobalScheduleDetail): string {
  const score = detail.score_display ?? detail.score
  const breakdown = detail.score_breakdown
  if (!breakdown) {
    return `综合评分 ${score}`
  }
  return `综合评分 ${score}（距离 ${breakdown.distance_component} + 时效 ${breakdown.time_component} + 货物 ${breakdown.goods_component}）`
}

function buildPathSummary(detail: GlobalScheduleDetail): string {
  const samples = detail.goods_schedules.slice(0, 3)
  if (!samples.length) return '暂无货物路径明细'
  return samples
    .map((g) => {
      const labels = g.path_labels?.length ? g.path_labels.join(' → ') : g.path.join(' → ')
      return `${g.goods_code}（订单 ${g.order_code}）：${labels}`
    })
    .join('；')
}

export async function mockExplainSchedule(
  payload: AiExplainRequest,
): Promise<AiExplainResult> {
  await delay(800)

  const detail = await getMockScheduleDetail(payload.schedule_code)
  if (!detail) {
    throw new Error(`调度方案不存在: ${payload.schedule_code}`)
  }

  const orderCount = detail.order_codes?.length ?? new Set(detail.goods_schedules.map((g) => g.order_code)).size
  const scoreLine = formatScoreLine(detail)
  const pathSummary = buildPathSummary(detail)
  const degraded = Boolean(detail.is_replan)

  if (payload.detail_level === 'brief') {
    const data: AiExplainData = {
      schedule_code: payload.schedule_code,
      explanation: `方案 ${payload.schedule_code}：${orderCount} 个订单、${detail.total_goods} 件货物；${scoreLine}。`,
    }
    return {
      data,
      meta: {
        degraded,
        degraded_reason: degraded ? 'Mock：DeepSeek 调用超时，已使用规则模板生成解释' : null,
      },
    }
  }

  const data: AiExplainData = {
    schedule_code: payload.schedule_code,
    explanation: [
      `本方案 ${payload.schedule_code} 覆盖 ${orderCount} 个订单、共 ${detail.total_goods} 件货物，`,
      `总距离约 ${detail.total_distance} km、预估时效 ${detail.total_time} h。`,
      `${scoreLine}。`,
      detail.is_replan ? '该方案为重规划结果，在保留原订单约束下调整了路径分配。' : '',
    ]
      .filter(Boolean)
      .join(''),
    sections: {
      reasoning: [
        '同订单货物尽量汇聚至同一 L1 分拣中心，减少二次拆包与转运成本。',
        `典型路径示例：${pathSummary}${detail.goods_schedules.length > 3 ? ' 等' : ''}。`,
      ].join(' '),
      risks: [
        detail.total_distance > 500 ? '总运输距离偏高，可能影响整体时效' : '部分节点间距离较长',
        detail.package_count != null && detail.package_count > 20 ? '包裹量较大，节点处理能力需关注' : '高峰时段可能存在排队',
      ],
      suggestions: [
        '可对远距离订单单独分批调度',
        '确认 L1 分拣中心容量与当前包裹量匹配',
      ],
    },
  }

  return {
    data,
    meta: {
      degraded,
      degraded_reason: degraded ? 'Mock：DeepSeek 调用超时，已使用规则模板生成解释' : null,
    },
  }
}
