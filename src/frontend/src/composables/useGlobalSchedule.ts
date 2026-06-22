import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createGlobalSchedule,
  getGlobalSchedule,
  listGlobalSchedules,
} from '@/api/schedule'
import type {
  GlobalScheduleDetail,
  GlobalScheduleSummary,
} from '@/types/schedule'

export function useGlobalSchedule() {
  const schedules = ref<GlobalScheduleSummary[]>([])
  const selectedCode = ref('')
  const summary = ref<GlobalScheduleSummary | null>(null)
  const detail = ref<GlobalScheduleDetail | null>(null)
  const listLoading = ref(false)
  const detailLoading = ref(false)
  const generating = ref(false)

  async function loadSchedules(selectCode?: string): Promise<void> {
    listLoading.value = true
    try {
      const result = await listGlobalSchedules({ page: 1, page_size: 100 })
      schedules.value = result.items
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
      summary.value = null
      detail.value = null
      return
    }

    detailLoading.value = true
    try {
      const data = await getGlobalSchedule(code)
      detail.value = data
      summary.value = data
    } catch (err) {
      detail.value = null
      summary.value = schedules.value.find((s) => s.schedule_code === code) ?? null
      ElMessage.error(err instanceof Error ? err.message : '加载方案详情失败')
    } finally {
      detailLoading.value = false
    }
  }

  async function generateSchedule(): Promise<void> {
    generating.value = true
    ElMessage.info('调度计算中，请稍候（最长约 10 秒）')
    try {
      const created = await createGlobalSchedule({
        algorithm: 'traditional',
      })
      await loadSchedules(created.schedule_code)
      ElMessage.success('全局调度方案已生成')
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '生成调度失败')
    } finally {
      generating.value = false
    }
  }

  watch(selectedCode, (code) => {
    void loadDetail(code)
  })

  return {
    schedules,
    selectedCode,
    summary,
    detail,
    listLoading,
    detailLoading,
    generating,
    loadSchedules,
    generateSchedule,
  }
}
