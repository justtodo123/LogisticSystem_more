import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  analyzeException,
  explainSchedule,
  parseAi,
  reviewSchedule,
} from '@/api/ai'
import type {
  AiExecuteMode,
  AiParseData,
  AiParseRequest,
  AiParseResult,
  AiResponseMeta,
  AiTargetMode,
  AlgorithmParams,
} from '@/types/ai'

const DEFAULT_WEIGHTS: AlgorithmParams = {
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

export function useAiParse(options: {
  selectedScheduleCode: () => string | undefined
  scheduleCodes: () => string[]
  onDraftCreated?: (scheduleCode: string) => void | Promise<void>
}) {
  const message = ref('')
  const targetMode = ref<AiTargetMode>('new')
  const multiScheduleCodes = ref<string[]>([])
  const weightsEnabled = ref(false)
  const weights = reactive<AlgorithmParams>(structuredClone(DEFAULT_WEIGHTS))

  const loading = ref(false)
  const lastResult = ref<AiParseData | null>(null)
  const lastMeta = ref<AiResponseMeta | null>(null)

  const canUseCurrentReplan = computed(
    () => Boolean(options.selectedScheduleCode()),
  )

  function buildScheduleCodes(): string[] | undefined {
    if (targetMode.value === 'new') return undefined
    if (targetMode.value === 'current') {
      const code = options.selectedScheduleCode()
      return code ? [code] : undefined
    }
    return multiScheduleCodes.value.length ? [...multiScheduleCodes.value] : undefined
  }

  function buildPayload(execute: AiExecuteMode): AiParseRequest {
    const payload: AiParseRequest = { execute }
    const trimmed = message.value.trim()
    if (trimmed) {
      payload.message = trimmed
    }
    const codes = buildScheduleCodes()
    if (codes?.length) {
      payload.schedule_codes = codes
    }
    if (weightsEnabled.value && weights.global_schedule) {
      payload.weights = {
        global_schedule: structuredClone(weights.global_schedule),
      }
    }
    return payload
  }

  function validateBeforeSend(execute: AiExecuteMode): boolean {
    if (targetMode.value === 'current' && !options.selectedScheduleCode()) {
      ElMessage.warning('请先在上方选择要重规划的方案')
      return false
    }
    if (targetMode.value === 'multi' && !multiScheduleCodes.value.length) {
      ElMessage.warning('请至少选择一个历史方案')
      return false
    }
    if (
      execute === 'draft' &&
      !message.value.trim() &&
      !weightsEnabled.value &&
      targetMode.value === 'new'
    ) {
      ElMessage.warning('请输入自然语言指令，或启用手动权重')
      return false
    }
    return true
  }

  async function handleResult(
    result: AiParseResult,
    execute: AiExecuteMode,
  ): Promise<void> {
    lastResult.value = result.data
    lastMeta.value = result.meta

    if (result.meta.degraded) {
      ElMessage.warning(
        result.meta.degraded_reason || 'DeepSeek 已降级，使用默认算法参数',
      )
    }

    if (execute === 'dry-run') {
      ElMessage.success('参数预览完成（未写入数据库）')
      return
    }

    if (result.data.status === 'draft' && result.data.schedule_code) {
      ElMessage.success(
        result.data.is_replan
          ? `AI 重规划预览已生成：${result.data.schedule_code}，请在上方确认采用`
          : `AI 预览方案已生成：${result.data.schedule_code}，请在上方确认采用`,
      )
      await options.onDraftCreated?.(result.data.schedule_code)
    }
  }

  async function submit(execute: AiExecuteMode): Promise<void> {
    if (loading.value) return
    if (!validateBeforeSend(execute)) return

    loading.value = true
    lastResult.value = null
    lastMeta.value = null
    try {
      const result = await parseAi(buildPayload(execute))
      await handleResult(result, execute)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'AI 调度失败'
      if (msg.includes('timeout') || msg.includes('超时')) {
        ElMessage.error('AI 调度计算超时，请稍后重试或检查后端')
      } else {
        ElMessage.error(msg)
      }
    } finally {
      loading.value = false
    }
  }

  async function tryP1(
    action: 'explain' | 'review' | 'analyze',
    scheduleCode?: string,
    exceptionCode?: string,
  ): Promise<void> {
    try {
      if (action === 'explain') {
        if (!scheduleCode) {
          ElMessage.warning('请先选择方案')
          return
        }
        await explainSchedule({ schedule_code: scheduleCode })
      } else if (action === 'review') {
        if (!scheduleCode) {
          ElMessage.warning('请先选择方案')
          return
        }
        await reviewSchedule({ schedule_code: scheduleCode })
      } else {
        if (!exceptionCode) {
          ElMessage.info('请在异常管理页选择事件后使用（P1 占位）')
          return
        }
        await analyzeException({ exception_event_code: exceptionCode })
      }
    } catch (err) {
      ElMessage.info(err instanceof Error ? err.message : '功能开发中（P1）')
    }
  }

  function resetWeights(): void {
    Object.assign(weights, structuredClone(DEFAULT_WEIGHTS))
  }

  return {
    message,
    targetMode,
    multiScheduleCodes,
    weightsEnabled,
    weights,
    loading,
    lastResult,
    lastMeta,
    canUseCurrentReplan,
    submit,
    tryP1,
    resetWeights,
  }
}
