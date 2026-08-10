import { h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { batchReplan, triggerReplan } from '@/api/exceptions'
import type {
  BatchReplanPayload,
  ExceptionEvent,
  RedispatchReplanResult,
  ReplanResult,
  ReplanStrategy,
} from '@/types/exception'

function isRedispatchResult(result: ReplanResult): result is RedispatchReplanResult {
  return 'new_schedule_code' in result || 'schedule_code' in result
}

const STRATEGY_OPTIONS: Array<{ value: ReplanStrategy; label: string; desc: string }> = [
  { value: 'full', label: '全部重排', desc: '对方案内所有订单重新调度' },
  { value: 'partial', label: '仅重排受影响', desc: '只对异常影响的订单重新调度' },
  { value: 'hybrid', label: '自动选择', desc: '根据受影响比例自动选择' },
]

/** 重规划策略选择（radio 组，redispatch 时展示） */
function renderStrategyRadios(strategyRef: { value: ReplanStrategy }) {
  return h(
    'div',
    { style: { padding: '4px 0 8px' } },
    STRATEGY_OPTIONS.map((s) =>
      h(
        'label',
        {
          style: {
            display: 'block',
            margin: '6px 0',
            cursor: 'pointer',
            fontSize: '13px',
          },
        },
        [
          h('input', {
            type: 'radio',
            name: 'replan-strategy',
            value: s.value,
            checked: s.value === 'full',
            onChange: (e: Event) => {
              strategyRef.value = (e.target as HTMLInputElement).value as ReplanStrategy
            },
          }),
          ` ${s.label}（${s.desc}）`,
        ],
      ),
    ),
  )
}

function formatDiff(diff?: RedispatchReplanResult['diff_summary']): string {
  if (!diff) return ''
  const etaText =
    diff.new_eta_delta > 0
      ? `总时长 +${diff.new_eta_delta}h`
      : `总时长 ${diff.new_eta_delta}h`
  const costText =
    diff.cost_delta > 0 ? `成本 +¥${diff.cost_delta}` : `成本 ¥${diff.cost_delta}`
  return `重排 ${diff.affected_count} 包裹；${etaText}；${costText}`
}

export function useExceptionReplan(onSuccess?: () => void | Promise<void>) {
  const router = useRouter()
  const replanningCode = ref('')
  const batchReplanning = ref(false)

  async function runReplan(event: ExceptionEvent): Promise<void> {
    if (event.status !== 'open') {
      ElMessage.warning('已解决的异常无法重规划')
      return
    }

    const action = event.recommended_action
    const actionLabel = action === 'redispatch' ? '重新调度 (redispatch)' : '重新规划路径 (reroute)'

    // 策略选择（仅 redispatch 生效）
    const strategyRef = { value: 'full' as ReplanStrategy }
    const message =
      action === 'redispatch'
        ? h('div', [
            h(
              'p',
              { style: { margin: '0 0 4px', color: '#909399', fontSize: '13px' } },
              '重规划策略：',
            ),
            renderStrategyRadios(strategyRef),
          ])
        : undefined

    let reason = event.description
    try {
      const { value } = await ElMessageBox.prompt(
        `确认对 ${event.event_code} 触发「${actionLabel}」？`,
        '触发重规划',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          inputValue: event.description,
          inputValidator: (v) => (v?.trim() ? true : '请填写重规划原因'),
          message,
        },
      )
      reason = value.trim()
    } catch {
      return
    }

    replanningCode.value = event.event_code
    ElMessage.info('重规划计算中，请稍候…')
    try {
      const result = await triggerReplan(event.event_code, {
        action,
        reason,
        strategy: action === 'redispatch' ? strategyRef.value : undefined,
      })
      if (isRedispatchResult(result)) {
        const code = result.new_schedule_code ?? result.schedule_code
        const diffText = formatDiff(result.diff_summary)
        ElMessage.success(
          `重规划完成，新方案 ${code}（v${result.version}）${diffText ? `｜${diffText}` : ''}`,
        )
        await router.push({ path: '/dashboard', query: { schedule: code } })
      } else {
        ElMessage.success(
          `路径重规划完成，新路线 ${result.new_route_code}（v${result.version}）`,
        )
        ElMessage.info('可在调度工作台查看同方案下的更新路线')
      }
      await onSuccess?.()
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '重规划失败')
    } finally {
      replanningCode.value = ''
    }
  }

  async function runBatchReplan(eventCodes: string[]): Promise<void> {
    if (eventCodes.length === 0) {
      ElMessage.warning('请选择至少一个待处理的异常事件')
      return
    }

    const strategyRef = { value: 'full' as ReplanStrategy }
    try {
      await ElMessageBox({
        title: '批量重规划',
        message: h('div', [
          h(
            'p',
            { style: { margin: '0 0 8px', color: '#909399', fontSize: '13px' } },
            `将按关联调度方案分组重规划，共 ${eventCodes.length} 个异常事件（同一方案只重规划一次）：`,
          ),
          renderStrategyRadios(strategyRef),
        ]),
        confirmButtonText: '确认重规划',
        cancelButtonText: '取消',
        showCancelButton: true,
        showInput: false,
      })
    } catch {
      return
    }

    batchReplanning.value = true
    ElMessage.info('批量重规划计算中，请稍候…')
    try {
      const payload: BatchReplanPayload = {
        event_codes: eventCodes,
        reason: '批量异常触发重规划',
        strategy: strategyRef.value,
      }
      const result = await batchReplan(payload)
      const ok = result.replanned_schedules.filter((r) => r.result_code === 0)
      if (ok.length > 0) {
        ElMessage.success(
          `批量重规划完成：${ok.length} 个方案已重排，跳过 ${result.skipped.length} 个无效事件`,
        )
      } else {
        ElMessage.warning('批量重规划未生成新方案，请检查异常事件是否有效')
      }
      await onSuccess?.()
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '批量重规划失败')
    } finally {
      batchReplanning.value = false
    }
  }

  return {
    replanningCode,
    batchReplanning,
    runReplan,
    runBatchReplan,
  }
}
