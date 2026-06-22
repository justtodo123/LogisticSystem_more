import { ref, watch, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createNodeDispatch,
  getDispatchBatch,
  listDispatchBatches,
} from '@/api/schedule'
import type {
  DispatchBatchDetail,
  DispatchBatchSummary,
} from '@/types/dispatch'

export function useNodeDispatch(selectedCode: Ref<string>) {
  const demoMode = ref(false)
  const batches = ref<DispatchBatchSummary[]>([])
  const selectedBatchCode = ref('')
  const batchDetail = ref<DispatchBatchDetail | null>(null)
  const batchListLoading = ref(false)
  const batchDetailLoading = ref(false)
  const dispatching = ref(false)

  async function loadBatches(scheduleCode?: string): Promise<void> {
    const code = scheduleCode ?? selectedCode.value
    if (!code) {
      batches.value = []
      selectedBatchCode.value = ''
      batchDetail.value = null
      return
    }

    batchListLoading.value = true
    try {
      const result = await listDispatchBatches({
        schedule_code: code,
        page: 1,
        page_size: 100,
      })
      batches.value = result.items
      if (
        selectedBatchCode.value &&
        result.items.some((b) => b.batch_code === selectedBatchCode.value)
      ) {
        // keep selection
      } else if (result.items.length > 0) {
        selectedBatchCode.value = result.items[0].batch_code
      } else {
        selectedBatchCode.value = ''
        batchDetail.value = null
      }
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '加载调度批次失败')
    } finally {
      batchListLoading.value = false
    }
  }

  async function loadBatchDetail(batchCode: string): Promise<void> {
    if (!batchCode) {
      batchDetail.value = null
      return
    }

    batchDetailLoading.value = true
    try {
      batchDetail.value = await getDispatchBatch(batchCode)
    } catch (err) {
      batchDetail.value = null
      ElMessage.error(err instanceof Error ? err.message : '加载批次详情失败')
    } finally {
      batchDetailLoading.value = false
    }
  }

  async function createDispatch(): Promise<void> {
    if (!selectedCode.value) {
      ElMessage.warning('请先选择全局调度方案')
      return
    }

    dispatching.value = true
    ElMessage.info('节点间调度计算中，请稍候')
    try {
      const result = await createNodeDispatch({
        schedule_code: selectedCode.value,
        demo_mode: demoMode.value,
      })
      await loadBatches(selectedCode.value)
      selectedBatchCode.value = result.batch_code
      await loadBatchDetail(result.batch_code)
      ElMessage.success(
        `节点间调度已生成：L0→L1 ${result.l0_l1_dispatch_count} 辆，L1→L2 ${result.l1_l2_dispatch_count} 辆`,
      )
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '生成节点间调度失败')
    } finally {
      dispatching.value = false
    }
  }

  async function refreshDispatch(): Promise<void> {
    await loadBatches(selectedCode.value)
    if (selectedBatchCode.value) {
      await loadBatchDetail(selectedBatchCode.value)
    }
  }

  watch(selectedCode, (code) => {
    void loadBatches(code)
  })

  watch(selectedBatchCode, (code) => {
    void loadBatchDetail(code)
  })

  return {
    demoMode,
    batches,
    selectedBatchCode,
    batchDetail,
    batchListLoading,
    batchDetailLoading,
    dispatching,
    loadBatches,
    createDispatch,
    refreshDispatch,
  }
}
