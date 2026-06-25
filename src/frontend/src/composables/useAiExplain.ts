import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { explainSchedule } from '@/api/ai'
import type { AiExplainData, AiResponseMeta } from '@/types/ai'

export function useAiExplain() {
  const loading = ref(false)
  const drawerVisible = ref(false)
  const result = ref<AiExplainData | null>(null)
  const meta = ref<AiResponseMeta | null>(null)
  const pendingMessage = ref<string | null>(null)
  const activeScheduleCode = ref<string | null>(null)

  async function explain(scheduleCode?: string): Promise<void> {
    if (loading.value) return

    if (!scheduleCode) {
      ElMessage.warning('请先在上方选择要解释的方案')
      return
    }

    loading.value = true
    pendingMessage.value = null
    result.value = null
    meta.value = null
    activeScheduleCode.value = scheduleCode

    try {
      const response = await explainSchedule({
        schedule_code: scheduleCode,
        detail_level: 'detailed',
      })

      meta.value = response.meta

      if (response.pending) {
        pendingMessage.value = response.message || 'F015 方案解释功能正在开发中（P1）'
        return
      }

      if (!response.data) {
        ElMessage.error('未收到解释内容')
        return
      }

      result.value = response.data
      drawerVisible.value = true

      if (response.meta.degraded) {
        ElMessage.warning(
          response.meta.degraded_reason || 'DeepSeek 已降级，展示模板解释',
        )
      }
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '方案解释失败')
    } finally {
      loading.value = false
    }
  }

  function closeDrawer(): void {
    drawerVisible.value = false
  }

  function clearPending(): void {
    pendingMessage.value = null
  }

  return {
    loading,
    drawerVisible,
    result,
    meta,
    pendingMessage,
    activeScheduleCode,
    explain,
    closeDrawer,
    clearPending,
  }
}
