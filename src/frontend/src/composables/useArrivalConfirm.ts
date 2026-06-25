import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { confirmArrival, getArrivalPackages } from '@/api/simulation'
import { listLevel1SortingCenters } from '@/api/nodes'
import { listGlobalSchedules } from '@/api/schedule'
import {
  ARRIVAL_DEMO_NODE,
  ARRIVAL_DEMO_SCHEDULE,
} from '@/constants/arrival'
import type {
  ArrivalPackageItem,
  ConfirmArrivalItem,
  ConfirmArrivalResult,
  PackageArrivalExceptionSubtype,
} from '@/types/simulation'
import type { GlobalScheduleSummary } from '@/types/schedule'
import type { NodeItem } from '@/types/node'
import { useMockSimulation } from '@/utils/env'
import {
  ensureArrivalScheduleRegistry,
  initMockArrivalDemoState,
} from '@/utils/mock-arrival-store'

export interface PackageSelection {
  result: 'normal' | 'exception' | ''
  exception_subtype: PackageArrivalExceptionSubtype | ''
  remark: string
}

export function useArrivalConfirm() {
  const schedules = ref<GlobalScheduleSummary[]>([])
  const nodes = ref<NodeItem[]>([])
  const scheduleCode = ref('')
  const nodeCode = ref('')
  const packages = ref<ArrivalPackageItem[]>([])
  const selections = ref<Record<string, PackageSelection>>({})
  const lastResult = ref<ConfirmArrivalResult | null>(null)

  const listLoading = ref(false)
  const nodesLoading = ref(false)
  const fetchLoading = ref(false)
  const submitLoading = ref(false)
  const initLoading = ref(false)

  const canSubmit = computed(() => {
    if (packages.value.length === 0) return false
    return packages.value.every((p) => {
      const sel = selections.value[p.package_code]
      if (!sel?.result) return false
      return true
    })
  })

  function resetSelections(items: ArrivalPackageItem[]): void {
    const next: Record<string, PackageSelection> = {}
    for (const pkg of items) {
      next[pkg.package_code] = {
        result: '',
        exception_subtype: '',
        remark: '',
      }
    }
    selections.value = next
  }

  async function loadSchedules(): Promise<void> {
    listLoading.value = true
    try {
      const result = await listGlobalSchedules({ page: 1, page_size: 100 })
      schedules.value = result.items.filter((s) => s.status !== 'draft')
      if (!scheduleCode.value && schedules.value.length > 0) {
        scheduleCode.value = schedules.value[0].schedule_code
      }
    } catch (err) {
      showError(err, '加载调度方案失败')
    } finally {
      listLoading.value = false
    }
  }

  async function loadNodes(): Promise<void> {
    if (!scheduleCode.value) {
      nodes.value = []
      return
    }
    nodesLoading.value = true
    try {
      nodes.value = await listLevel1SortingCenters()
      if (!nodeCode.value && nodes.value.length > 0) {
        const preferred = nodes.value.find((n) => n.node_code === ARRIVAL_DEMO_NODE)
        nodeCode.value = preferred?.node_code ?? nodes.value[0].node_code
      }
    } catch (err) {
      showError(err, '加载节点列表失败')
    } finally {
      nodesLoading.value = false
    }
  }

  async function initDemoData(): Promise<void> {
    if (!useMockSimulation()) {
      ElMessage.warning('演示数据初始化仅 Mock 模式可用')
      return
    }
    initLoading.value = true
    try {
      await initMockArrivalDemoState(
        scheduleCode.value || ARRIVAL_DEMO_SCHEDULE,
        nodeCode.value || ARRIVAL_DEMO_NODE,
      )
      scheduleCode.value = ARRIVAL_DEMO_SCHEDULE
      nodeCode.value = ARRIVAL_DEMO_NODE
      ElMessage.success('演示数据已初始化（C/D in_transit，E/F pending_pack）')
      await fetchPackages()
    } catch (err) {
      showError(err, '初始化演示数据失败')
    } finally {
      initLoading.value = false
    }
  }

  async function fetchPackages(): Promise<void> {
    if (!scheduleCode.value || !nodeCode.value) {
      ElMessage.warning('请先选择调度方案与到站节点')
      return
    }
    fetchLoading.value = true
    lastResult.value = null
    try {
      ensureArrivalScheduleRegistry(scheduleCode.value)
      const data = await getArrivalPackages({
        schedule_code: scheduleCode.value,
        node_code: nodeCode.value,
      })
      packages.value = data.packages
      resetSelections(data.packages)
      if (data.packages.length === 0) {
        ElMessage.info('当前节点暂无待确认到站包裹')
      }
    } catch (err) {
      showError(err, '加载待确认包裹失败')
    } finally {
      fetchLoading.value = false
    }
  }

  async function submit(): Promise<void> {
    if (!canSubmit.value) {
      ElMessage.warning('请为每条包裹选择正常或异常')
      return
    }
    submitLoading.value = true
    try {
      const items: ConfirmArrivalItem[] = packages.value.map((p) => {
        const sel = selections.value[p.package_code]
        const item: ConfirmArrivalItem = {
          package_code: p.package_code,
          result: sel.result as 'normal' | 'exception',
        }
        if (sel.result === 'exception') {
          if (sel.exception_subtype) {
            item.exception_subtype = sel.exception_subtype
          }
          if (sel.remark.trim()) {
            item.remark = sel.remark.trim()
          }
        }
        return item
      })

      const result = await confirmArrival({
        schedule_code: scheduleCode.value,
        node_code: nodeCode.value,
        items,
      })
      lastResult.value = result
      ElMessage.success('到站确认成功')
      await fetchPackages()
    } catch (err) {
      showError(err, '到站确认失败')
    } finally {
      submitLoading.value = false
    }
  }

  function showError(err: unknown, fallback: string): void {
    const message = err instanceof Error ? err.message : fallback
    if (message.includes('403') || message.includes('调度员') || message.includes('dispatcher')) {
      ElMessage.error('仅调度员可执行到站确认')
      return
    }
    if (message.includes('in_transit') || message.includes('40001')) {
      ElMessage.error('包裹状态不符或已确认，请刷新列表后重试')
      return
    }
    ElMessage.error(message || fallback)
  }

  return {
    schedules,
    nodes,
    scheduleCode,
    nodeCode,
    packages,
    selections,
    lastResult,
    listLoading,
    nodesLoading,
    fetchLoading,
    submitLoading,
    initLoading,
    canSubmit,
    loadSchedules,
    loadNodes,
    initDemoData,
    fetchPackages,
    submit,
  }
}
