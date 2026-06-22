import { ref, watch, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getVehicleRouteCoordinates, planRoutes as planRoutesApi } from '@/api/routes'
import { routeColorForIndex } from '@/constants/route-colors'
import type { DispatchBatchDetail } from '@/types/dispatch'
import type { RouteCoordinates, RoutePackagePoint, SelectedPackageDetail } from '@/types/route'
import { useMockRoutes } from '@/utils/env'
import {
  listRouteVehicles,
  type RouteVehicleOption,
} from '@/utils/route-vehicles'

export function useRouteVisualization(batchDetail: Ref<DispatchBatchDetail | null>) {
  const vehicles = ref<RouteVehicleOption[]>([])
  const selectedVehicleCode = ref('')
  const coordinates = ref<RouteCoordinates | null>(null)
  const loading = ref(false)
  const planning = ref(false)
  const selectedVehicleIndex = ref(0)
  const drawerVisible = ref(false)
  const selectedPackage = ref<SelectedPackageDetail | null>(null)

  const strokeColor = ref(routeColorForIndex(0))

  function resetRouteState(): void {
    selectedVehicleCode.value = ''
    coordinates.value = null
    selectedVehicleIndex.value = 0
    strokeColor.value = routeColorForIndex(0)
    selectedPackage.value = null
    drawerVisible.value = false
  }

  function syncVehicles(): void {
    vehicles.value = listRouteVehicles(batchDetail.value)
    resetRouteState()
    if (vehicles.value.length > 0) {
      void selectVehicle(vehicles.value[0].vehicle_code, 0)
    }
  }

  async function selectVehicle(vehicleCode: string, index: number): Promise<void> {
    if (!vehicleCode) return
    selectedVehicleCode.value = vehicleCode
    selectedVehicleIndex.value = index
    strokeColor.value = routeColorForIndex(index)

    const option = vehicles.value.find((v) => v.vehicle_code === vehicleCode)
    loading.value = true
    try {
      coordinates.value = await getVehicleRouteCoordinates(vehicleCode, {
        batchCode: batchDetail.value?.batch_code,
        dispatch: option?.dispatch ?? null,
      })
    } catch (err) {
      coordinates.value = null
      ElMessage.error(err instanceof Error ? err.message : '加载路线失败')
    } finally {
      loading.value = false
    }
  }

  function onPackageClick(pkg: RoutePackagePoint): void {
    if (!coordinates.value) return
    const dispatch = vehicles.value.find(
      (v) => v.vehicle_code === selectedVehicleCode.value,
    )?.dispatch
    let fromNode: string | undefined
    let toNode: string | undefined
    for (const task of dispatch?.tasks ?? []) {
      if (task.package_codes.includes(pkg.package_code)) {
        fromNode = task.from_node_code
        toNode = task.to_node_code
        break
      }
    }
    selectedPackage.value = {
      package_code: pkg.package_code,
      route_code: coordinates.value.route_code,
      from_node_code: fromNode,
      to_node_code: toNode,
      total_distance: coordinates.value.total_distance,
      total_time: coordinates.value.total_time,
    }
    drawerVisible.value = true
  }

  async function planRoutes(): Promise<void> {
    const batchCode = batchDetail.value?.batch_code
    if (!batchCode || !vehicles.value.length) {
      ElMessage.warning('请先生成节点间调度')
      return
    }

    planning.value = true
    ElMessage.info('路径规划计算中，请稍候')
    try {
      const result = await planRoutesApi(batchCode)
      ElMessage.success(`路径规划完成：${result.routes.length} 条路线`)
      if (selectedVehicleCode.value) {
        await selectVehicle(selectedVehicleCode.value, selectedVehicleIndex.value)
      } else if (vehicles.value.length > 0) {
        await selectVehicle(vehicles.value[0].vehicle_code, 0)
      }
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '路径规划失败')
    } finally {
      planning.value = false
    }
  }

  watch(batchDetail, () => {
    syncVehicles()
  }, { immediate: true })

  watch(selectedVehicleCode, (code) => {
    if (!code) return
    const idx = vehicles.value.findIndex((v) => v.vehicle_code === code)
    if (idx >= 0 && idx !== selectedVehicleIndex.value) {
      void selectVehicle(code, idx)
    }
  })

  return {
    vehicles,
    selectedVehicleCode,
    coordinates,
    loading,
    planning,
    strokeColor,
    drawerVisible,
    selectedPackage,
    selectVehicle,
    planRoutes,
    onPackageClick,
    showPlanButton: !useMockRoutes(),
  }
}
