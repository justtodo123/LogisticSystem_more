<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import DispatchBatchPanel from '@/components/schedule/DispatchBatchPanel.vue'
import GoodsPathTable from '@/components/schedule/GoodsPathTable.vue'
import ScheduleSummaryCards from '@/components/schedule/ScheduleSummaryCards.vue'
import VehicleTaskTable from '@/components/schedule/VehicleTaskTable.vue'
import VehicleRoutePicker from '@/components/schedule/VehicleRoutePicker.vue'
import RouteMap from '@/components/schedule/RouteMap.vue'
import { useGlobalSchedule } from '@/composables/useGlobalSchedule'
import { useNodeDispatch } from '@/composables/useNodeDispatch'
import { useRouteVisualization } from '@/composables/useRouteVisualization'
import { useSimulationDelivery } from '@/composables/useSimulationDelivery'

const authStore = useAuthStore()

const {
  schedules,
  selectedCode,
  summary,
  detail,
  listLoading,
  detailLoading,
  generating,
  loadSchedules,
  generateSchedule,
} = useGlobalSchedule()

const {
  demoMode,
  batches,
  selectedBatchCode,
  batchDetail,
  batchListLoading,
  batchDetailLoading,
  dispatching,
  createDispatch,
  refreshDispatch,
} = useNodeDispatch(selectedCode)

const {
  vehicles: routeVehicles,
  selectedVehicleCode,
  coordinates: routeCoordinates,
  loading: routeLoading,
  planning: routePlanning,
  strokeColor: routeStrokeColor,
  drawerVisible: packageDrawerVisible,
  selectedPackage,
  planRoutes,
  onPackageClick,
  showPlanButton,
} = useRouteVisualization(batchDetail)

const {
  delivering: simulationDelivering,
  canDeliver,
  deliverAll,
  deliverVehicle,
  deliverPackage,
} = useSimulationDelivery({
  batchDetail,
  selectedVehicleCode,
  onSuccess: refreshDispatch,
})

onMounted(() => {
  void loadSchedules()
})
</script>

<template>
  <div class="dashboard page-card">
    <div class="dashboard-header">
      <div>
        <h2 class="dashboard-title">调度工作台</h2>
        <p class="dashboard-desc">
          欢迎，{{ authStore.displayName }}（{{ authStore.role }}）
        </p>
      </div>
      <div class="dashboard-toolbar">
        <el-button
          v-if="authStore.isDispatcher"
          type="primary"
          :loading="generating"
          :disabled="generating"
          @click="generateSchedule"
        >
          生成全局调度
        </el-button>
        <el-tag v-else type="info">只读模式</el-tag>
        <el-select
          v-model="selectedCode"
          placeholder="选择历史方案"
          clearable
          filterable
          :loading="listLoading"
          style="width: 240px"
          :disabled="!schedules.length"
        >
          <el-option
            v-for="item in schedules"
            :key="item.schedule_code"
            :label="`${item.schedule_code}（${item.created_at ?? ''}）`"
            :value="item.schedule_code"
          />
        </el-select>
      </div>
    </div>

    <el-empty
      v-if="!listLoading && !schedules.length"
      description="暂无调度方案，请先生成全局调度"
    />

    <template v-else>
      <ScheduleSummaryCards
        :summary="summary"
        :loading="detailLoading && !summary"
      />
      <div class="dashboard-body">
        <GoodsPathTable
          :items="detail?.goods_schedules ?? []"
          :loading="detailLoading"
        />
      </div>

      <el-divider content-position="left">节点间调度</el-divider>

      <div v-if="authStore.isDispatcher" class="dispatch-toolbar">
        <el-tooltip content="课堂演示：跳过 L1 等待，一次看到 L0→L1 与 L1→L2 任务">
          <div class="demo-switch">
            <span>demo_mode</span>
            <el-switch v-model="demoMode" />
          </div>
        </el-tooltip>
        <el-button
          type="success"
          :loading="dispatching"
          :disabled="dispatching || !selectedCode"
          @click="createDispatch"
        >
          生成节点间调度
        </el-button>
      </div>

      <DispatchBatchPanel
        v-model:selected-batch-code="selectedBatchCode"
        :batches="batches"
        :loading="batchListLoading"
      />

      <VehicleTaskTable
        :detail="batchDetail"
        :loading="batchDetailLoading"
      />

      <div
        v-if="authStore.isDispatcher && batchDetail"
        class="simulation-toolbar"
      >
        <el-tooltip
          content="demo_mode=false 时分阶段演示：L0→L1 调度与路径规划后模拟送达，再生成 L1→L2 调度并再次送达"
          placement="top"
        >
          <span class="simulation-hint">模拟送达（F013-1）</span>
        </el-tooltip>
        <el-button
          type="primary"
          plain
          :loading="simulationDelivering"
          :disabled="simulationDelivering || !canDeliver"
          @click="deliverAll"
        >
          全部送达
        </el-button>
        <el-button
          type="primary"
          plain
          :loading="simulationDelivering"
          :disabled="simulationDelivering || !canDeliver || !selectedVehicleCode"
          @click="deliverVehicle()"
        >
          当前车辆送达
        </el-button>
      </div>

      <el-divider content-position="left">路线可视化</el-divider>

      <div
        v-if="authStore.isDispatcher && showPlanButton"
        class="route-toolbar"
      >
        <el-button
          type="warning"
          plain
          :loading="routePlanning"
          :disabled="routePlanning || !batchDetail?.batch_code || !routeVehicles.length"
          @click="planRoutes"
        >
          路径规划
        </el-button>
      </div>

      <VehicleRoutePicker
        v-model:selected-vehicle-code="selectedVehicleCode"
        :vehicles="routeVehicles"
        :loading="routeLoading || batchDetailLoading"
      />

      <RouteMap
        :data="routeCoordinates"
        :loading="routeLoading"
        :stroke-color="routeStrokeColor"
        @package-click="onPackageClick"
      />

      <el-drawer
        v-model="packageDrawerVisible"
        title="包裹详情"
        size="320px"
        destroy-on-close
      >
        <el-descriptions v-if="selectedPackage" :column="1" border size="small">
          <el-descriptions-item label="包裹编号">
            {{ selectedPackage.package_code }}
          </el-descriptions-item>
          <el-descriptions-item label="路线编号">
            {{ selectedPackage.route_code }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedPackage.from_node_code" label="起点">
            {{ selectedPackage.from_node_code }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedPackage.to_node_code" label="终点">
            {{ selectedPackage.to_node_code }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedPackage.total_distance != null" label="总距离">
            {{ selectedPackage.total_distance.toFixed(1) }} km
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedPackage.total_time != null" label="总时间">
            {{ selectedPackage.total_time.toFixed(0) }} min
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="authStore.isDispatcher && selectedPackage" class="drawer-actions">
          <el-button
            type="primary"
            plain
            :loading="simulationDelivering"
            :disabled="simulationDelivering || !canDeliver"
            @click="deliverPackage(selectedPackage.package_code)"
          >
            模拟送达此包裹
          </el-button>
        </div>
      </el-drawer>
    </template>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.dashboard-title {
  margin: 0 0 8px;
  font-size: 20px;
}

.dashboard-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.dashboard-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.dashboard-body {
  margin-top: 20px;
}

.dispatch-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.demo-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.route-toolbar {
  margin-bottom: 12px;
}

.simulation-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.simulation-hint {
  font-size: 13px;
  color: #606266;
}

.drawer-actions {
  margin-top: 16px;
}
</style>
