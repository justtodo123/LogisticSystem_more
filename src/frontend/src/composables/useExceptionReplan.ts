import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { triggerReplan } from '@/api/exceptions'
import type {
  ExceptionEvent,
  RedispatchReplanResult,
  ReplanResult,
} from '@/types/exception'

function isRedispatchResult(result: ReplanResult): result is RedispatchReplanResult {
  return 'new_schedule_code' in result || 'schedule_code' in result
}

export function useExceptionReplan(onSuccess?: () => void | Promise<void>) {
  const router = useRouter()
  const replanningCode = ref('')

  async function runReplan(event: ExceptionEvent): Promise<void> {
    if (event.status !== 'open') {
      ElMessage.warning('已解决的异常无法重规划')
      return
    }

    const action = event.recommended_action
    const actionLabel = action === 'redispatch' ? '重新调度 (redispatch)' : '重新规划路径 (reroute)'

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
        },
      )
      reason = value.trim()
    } catch {
      return
    }

    replanningCode.value = event.event_code
    ElMessage.info('重规划计算中，请稍候…')
    try {
      const result = await triggerReplan(event.event_code, { action, reason })
      if (isRedispatchResult(result)) {
        const code = result.new_schedule_code ?? result.schedule_code
        ElMessage.success(`重规划完成，新方案 ${code}（v${result.version}）`)
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

  return {
    replanningCode,
    runReplan,
  }
}
