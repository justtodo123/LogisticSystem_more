import { computed, ref, watch, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { simulateDeliver } from '@/api/simulation'
import type { DispatchBatchDetail } from '@/types/dispatch'
import { useMockSimulation } from '@/utils/env'
import { countInTransitPackagesInBatch } from '@/utils/mock-simulation'

export function useSimulationDelivery(options: {
  batchDetail: Ref<DispatchBatchDetail | null>
  selectedVehicleCode: Ref<string>
  onSuccess?: () => Promise<void>
}) {
  const delivering = ref(false)
  const inTransitCount = ref(0)

  const canDeliver = computed(() => {
    const batch = options.batchDetail.value
    if (!batch || batch.status === 'completed' || batch.status === 'failed') {
      return false
    }
    if (useMockSimulation()) {
      return inTransitCount.value > 0
    }
    return batch.dispatches.length > 0
  })

  async function refreshInTransitCount(): Promise<void> {
    if (!useMockSimulation()) {
      inTransitCount.value = options.batchDetail.value ? 1 : 0
      return
    }
    inTransitCount.value = await countInTransitPackagesInBatch(
      options.batchDetail.value,
    )
  }

  watch(
    () => options.batchDetail.value,
    () => {
      void refreshInTransitCount()
    },
    { immediate: true },
  )

  function basePayload() {
    const batch = options.batchDetail.value
    return batch?.batch_code ? { batch_code: batch.batch_code } : {}
  }

  async function runDeliver(
    payload: { vehicle_code?: string; package_code?: string },
    confirmMessage?: string,
  ): Promise<void> {
    if (!canDeliver.value) {
      ElMessage.warning('当前无可送达的运输中包裹')
      return
    }

    if (confirmMessage) {
      try {
        await ElMessageBox.confirm(confirmMessage, '模拟送达', {
          type: 'warning',
          confirmButtonText: '确认送达',
          cancelButtonText: '取消',
        })
      } catch {
        return
      }
    }

    delivering.value = true
    try {
      const result = await simulateDeliver({ ...basePayload(), ...payload })
      ElMessage.success(
        result.message ?? `已模拟送达 ${result.packages_delivered} 个包裹`,
      )
      await options.onSuccess?.()
      await refreshInTransitCount()
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '模拟送达失败')
    } finally {
      delivering.value = false
    }
  }

  async function deliverAll(): Promise<void> {
    await runDeliver({}, '确认模拟送达当前批次内全部运输中包裹？')
  }

  async function deliverVehicle(vehicleCode?: string): Promise<void> {
    const code = vehicleCode || options.selectedVehicleCode.value
    if (!code) {
      ElMessage.warning('请先选择车辆')
      return
    }
    await runDeliver(
      { vehicle_code: code },
      `确认模拟送达车辆 ${code} 的运输中包裹？`,
    )
  }

  async function deliverPackage(packageCode: string): Promise<void> {
    if (!packageCode) return
    await runDeliver(
      { package_code: packageCode },
      `确认模拟送达包裹 ${packageCode}？`,
    )
  }

  return {
    delivering,
    canDeliver,
    inTransitCount,
    refreshInTransitCount,
    deliverAll,
    deliverVehicle,
    deliverPackage,
  }
}
