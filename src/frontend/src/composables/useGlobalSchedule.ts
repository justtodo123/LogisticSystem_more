import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  confirmGlobalSchedule,
  discardDraftSchedule,
  getGlobalSchedule,
  listGlobalSchedules,
  previewGlobalSchedule,
} from '@/api/schedule'
import type {
  GlobalScheduleDetail,
  GlobalScheduleSummary,
} from '@/types/schedule'

export function useGlobalSchedule() {
  const schedules = ref<GlobalScheduleSummary[]>([])
  const selectedCode = ref('')
  const previewCode = ref<string | null>(null)
  const summary = ref<GlobalScheduleSummary | null>(null)
  const detail = ref<GlobalScheduleDetail | null>(null)
  const listLoading = ref(false)
  const detailLoading = ref(false)
  const generating = ref(false)

  const isDraft = computed(() => summary.value?.status === 'draft')
  const viewingCode = computed(() =>
    isDraft.value ? previewCode.value ?? '' : selectedCode.value,
  )

  async function loadSchedules(selectCode?: string): Promise<void> {
    listLoading.value = true
    try {
      const result = await listGlobalSchedules({ page: 1, page_size: 100 })
      schedules.value = result.items
      if (isDraft.value) {
        return
      }
      if (selectCode && result.items.some((s) => s.schedule_code === selectCode)) {
        selectedCode.value = selectCode
      } else if (!selectedCode.value && result.items.length > 0) {
        selectedCode.value = result.items[0].schedule_code
      } else if (
        selectedCode.value &&
        !result.items.some((s) => s.schedule_code === selectedCode.value)
      ) {
        selectedCode.value = result.items[0]?.schedule_code ?? ''
      }
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '加载调度方案失败')
    } finally {
      listLoading.value = false
    }
  }

  async function loadDetail(code: string): Promise<void> {
    if (!code) {
      if (!isDraft.value) {
        summary.value = null
        detail.value = null
      }
      return
    }

    detailLoading.value = true
    try {
      const data = await getGlobalSchedule(code)
      detail.value = data
      summary.value = data
    } catch (err) {
      detail.value = null
      summary.value =
        schedules.value.find((s) => s.schedule_code === code) ?? null
      ElMessage.error(err instanceof Error ? err.message : '加载方案详情失败')
    } finally {
      detailLoading.value = false
    }
  }

  function resetPreviewState(): void {
    previewCode.value = null
    summary.value = null
    detail.value = null
  }

  async function applyAiDraftPreview(code: string): Promise<void> {
    previewCode.value = code
    await loadDetail(code)
  }

  async function ensureNoExistingDraft(): Promise<boolean> {
    if (!isDraft.value || !previewCode.value) return true
    try {
      await ElMessageBox.confirm(
        '当前已有预览方案，生成新预览将丢弃现有 draft，是否继续？',
        '丢弃预览',
        { type: 'warning', confirmButtonText: '继续', cancelButtonText: '取消' },
      )
      await discardDraft()
      return true
    } catch {
      return false
    }
  }

  async function previewSchedule(orderCodes?: string[]): Promise<void> {
    if (!(await ensureNoExistingDraft())) return

    generating.value = true
    ElMessage.info('调度计算中，请稍候（最长约 10 秒）')
    try {
      const created = await previewGlobalSchedule({
        algorithm: 'traditional',
        preview: true,
        ...(orderCodes?.length ? { order_codes: orderCodes } : {}),
      })
      previewCode.value = created.schedule_code
      await loadDetail(created.schedule_code)
      ElMessage.success('预览方案已生成，请确认采用或丢弃')
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '生成预览失败')
    } finally {
      generating.value = false
    }
  }

  async function confirmSchedule(): Promise<void> {
    const code = previewCode.value
    if (!code) {
      ElMessage.warning('没有可确认的预览方案')
      return
    }

    generating.value = true
    try {
      const confirmed = await confirmGlobalSchedule(code)
      resetPreviewState()
      await loadSchedules(confirmed.schedule_code)
      ElMessage.success('方案已确认采用')
    } catch (err) {
      resetPreviewState()
      ElMessage.error(err instanceof Error ? err.message : '确认失败，请重新预览')
    } finally {
      generating.value = false
    }
  }

  async function discardDraft(): Promise<void> {
    const code = previewCode.value
    if (!code) {
      resetPreviewState()
      return
    }

    generating.value = true
    try {
      await discardDraftSchedule(code)
      resetPreviewState()
      ElMessage.success('预览方案已丢弃')
    } catch (err) {
      resetPreviewState()
      ElMessage.error(err instanceof Error ? err.message : '丢弃预览失败')
    } finally {
      generating.value = false
    }
  }

  async function discardDraftWithConfirm(): Promise<void> {
    try {
      await ElMessageBox.confirm('确定丢弃当前预览方案？', '丢弃预览', {
        type: 'warning',
        confirmButtonText: '丢弃',
        cancelButtonText: '取消',
      })
      await discardDraft()
    } catch {
      // cancelled
    }
  }

  watch(viewingCode, (code) => {
    void loadDetail(code)
  })

  return {
    schedules,
    selectedCode,
    previewCode,
    summary,
    detail,
    listLoading,
    detailLoading,
    generating,
    isDraft,
    viewingCode,
    loadSchedules,
    previewSchedule,
    confirmSchedule,
    discardDraft,
    discardDraftWithConfirm,
    applyAiDraftPreview,
    resetPreviewState,
  }
}
