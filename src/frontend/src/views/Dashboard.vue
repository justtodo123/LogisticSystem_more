<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DispatchBatchPanel from '@/components/schedule/DispatchBatchPanel.vue'
import GoodsPathTable from '@/components/schedule/GoodsPathTable.vue'
import OrderSelectPanel from '@/components/schedule/OrderSelectPanel.vue'
import ScheduleSummaryCards from '@/components/schedule/ScheduleSummaryCards.vue'
import VehicleTaskTable from '@/components/schedule/VehicleTaskTable.vue'
import VehicleRoutePicker from '@/components/schedule/VehicleRoutePicker.vue'
import RouteMap from '@/components/schedule/RouteMap.vue'
import RouteDetailMeta from '@/components/schedule/RouteDetailMeta.vue'
import SchedulePackagesPanel from '@/components/schedule/SchedulePackagesPanel.vue'
import UnallocatedAlert from '@/components/schedule/UnallocatedAlert.vue'
import AiAssistantPanel from '@/components/ai/AiAssistantPanel.vue'
import EntityDetailDrawer from '@/components/detail/EntityDetailDrawer.vue'
import GoodsDetailBody from '@/components/detail/GoodsDetailBody.vue'
import OrderDetailBody from '@/components/detail/OrderDetailBody.vue'
import PackageDetailBody from '@/components/detail/PackageDetailBody.vue'
import DispatchDetailBody from '@/components/schedule/DispatchDetailBody.vue'
import { useGlobalSchedule } from '@/composables/useGlobalSchedule'
import { useNodeDispatch } from '@/composables/useNodeDispatch'
import { useRouteVisualization } from '@/composables/useRouteVisualization'
import { useSimulationDelivery } from '@/composables/useSimulationDelivery'
import { useDashboardDetail } from '@/composables/useDashboardDetail'
import type { GlobalScheduleSummary } from '@/types/schedule'

const authStore = useAuthStore()
const route = useRoute()
const selectedOrderCodes = ref<string[]>([])

const {
  schedules,
  selectedCode,
  previewCode,
  summary,
  detail,
  listLoading,
  detailLoading,
  generating,
  isDraft,
  loadSchedules,
  previewSchedule,
  confirmSchedule,
  discardDraftWithConfirm,
  applyAiDraftPreview,
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

const {
  goodsDetail,
  orderDetail,
  packageDetail,
  dispatchVisible,
  dispatchData,
  openGoods,
  openOrder,
  openDispatch,
  closeDispatch,
} = useDashboardDetail()

const {
  visible: goodsDrawerVisible,
  loading: goodsDrawerLoading,
  data: goodsDrawerData,
  title: goodsDrawerTitle,
} = goodsDetail

const {
  visible: orderDrawerVisible,
  loading: orderDrawerLoading,
  data: orderDrawerData,
  title: orderDrawerTitle,
} = orderDetail

const {
  visible: packageDrawerVisibleEntity,
  loading: packageDrawerLoading,
  data: packageDrawerData,
  title: packageDrawerTitle,
} = packageDetail

function scheduleOptionLabel(item: GlobalScheduleSummary): string {
  const parts: string[] = [item.schedule_code]
  if (item.version != null) {
    parts.push(`v${item.version}`)
  }
  if (item.is_replan) {
    parts.push('重规划')
  }
  if (item.created_at) {
    parts.push(item.created_at)
  }
  return parts.join(' · ')
}

function onOrderSelectionChange(codes: string[]): void {
  selectedOrderCodes.value = codes
}

onMounted(() => {
  const scheduleFromQuery = route.query.schedule
  const code =
    typeof scheduleFromQuery === 'string' ? scheduleFromQuery : undefined
  void loadSchedules(code)
})

async function onAiDraftCreated(scheduleCode: string): Promise<void> {
  await applyAiDraftPreview(scheduleCode)
}
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
        <template v-if="authStore.isDispatcher">
          <el-button
            type="primary"
            :loading="generating"
            :disabled="generating"
            @click="previewSchedule(selectedOrderCodes)"
          >
            生成预览
          </el-button>
          <el-button
            v-if="isDraft"
            type="success"
            :loading="generating"
            :disabled="generating"
            @click="confirmSchedule"
          >
            确认采用
          </el-button>
          <el-button
            v-if="isDraft"
            type="danger"
            plain
            :loading="generating"
            :disabled="generating"
            @click="discardDraftWithConfirm"
          >
            丢弃预览
          </el-button>
          <el-tag v-if="isDraft && previewCode" type="warning">
            当前预览：{{ previewCode }}
          </el-tag>
        </template>
        <el-tag v-else type="info">只读模式</el-tag>
        <el-select
          v-model="selectedCode"
          placeholder="选择历史方案"
          clearable
          filterable
          :loading="listLoading"
          style="width: 320px"
          :disabled="isDraft || !schedules.length"
        >
          <el-option
            v-for="item in schedules"
            :key="item.schedule_code"
            :label="scheduleOptionLabel(item)"
            :value="item.schedule_code"
          >
            <span>{{ item.schedule_code }}</span>
            <el-tag
              v-if="item.is_replan"
              type="warning"
              size="small"
              style="margin-left: 8px"
            >
              重规划
            </el-tag>
            <span
              v-if="item.version != null"
              style="margin-left: 6px; color: #909399; font-size: 12px"
            >
              v{{ item.version }}
            </span>
          </el-option>
        </el-select>
      </div>
    </div>

    <OrderSelectPanel
      v-if="authStore.isDispatcher"
      @selection-change="onOrderSelectionChange"
    />

    <el-empty
      v-if="!listLoading && !schedules.length && !isDraft"
      description="选择订单并生成预览，或从历史方案中选择"
    />

    <template v-else>
      <el-alert
        v-if="isDraft"
        type="warning"
        title="预览方案，尚未落库；确认采用后订单状态才会更新"
        show-icon
        :closable="false"
        class="draft-alert"
      />

      <ScheduleSummaryCards
        :summary="summary"
        :loading="detailLoading && !summary"
        :is-draft="isDraft"
      />
      <SchedulePackagesPanel
        :packages="detail?.packages"
        :loading="detailLoading"
        :is-draft="isDraft"
        @open-goods="openGoods"
      />
      <div class="dashboard-body">
        <GoodsPathTable
          :items="detail?.goods_schedules ?? []"
          :loading="detailLoading"
          @open-goods="openGoods"
          @open-order="openOrder"
        />
      </div>

      <el-divider content-position="left">节点间调度</el-divider>

      <div v-if="authStore.isDispatcher" class="dispatch-toolbar">
        <el-tooltip content="课堂演示：跳过 L1 等待，一次看到 L0→L1 与 L1→L2 任务">
          <div class="demo-switch">
            <span>demo_mode</span>
            <el-switch v-model="demoMode" :disabled="isDraft" />
          </div>
        </el-tooltip>
        <el-button
          type="success"
          :loading="dispatching"
          :disabled="dispatching || !selectedCode || isDraft"
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
        @open-dispatch="openDispatch"
      />

      <UnallocatedAlert :codes="batchDetail?.unallocated_packages" />

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
          :disabled="simulationDelivering || !canDeliver || isDraft"
          @click="deliverAll"
        >
          全部送达
        </el-button>
        <el-button
          type="primary"
          plain
          :loading="simulationDelivering"
          :disabled="simulationDelivering || !canDeliver || !selectedVehicleCode || isDraft"
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
          :disabled="routePlanning || !batchDetail?.batch_code || !routeVehicles.length || isDraft"
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

      <RouteDetailMeta :coordinates="routeCoordinates" />

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
            :disabled="simulationDelivering || !canDeliver || isDraft"
            @click="deliverPackage(selectedPackage.package_code)"
          >
            模拟送达此包裹
          </el-button>
        </div>
      </el-drawer>

      <EntityDetailDrawer
        v-model="goodsDrawerVisible"
        :title="goodsDrawerTitle"
        :loading="goodsDrawerLoading"
      >
        <GoodsDetailBody v-if="goodsDrawerData" :data="goodsDrawerData" />
      </EntityDetailDrawer>

      <EntityDetailDrawer
        v-model="orderDrawerVisible"
        :title="orderDrawerTitle"
        :loading="orderDrawerLoading"
      >
        <OrderDetailBody v-if="orderDrawerData" :data="orderDrawerData" />
      </EntityDetailDrawer>

      <EntityDetailDrawer
        v-model="packageDrawerVisibleEntity"
        :title="packageDrawerTitle"
        :loading="packageDrawerLoading"
      >
        <PackageDetailBody v-if="packageDrawerData" :data="packageDrawerData" />
      </EntityDetailDrawer>

      <EntityDetailDrawer
        v-model="dispatchVisible"
        :title="dispatchData ? `调度 · ${dispatchData.dispatch_code}` : '调度详情'"
        @update:model-value="(v) => !v && closeDispatch()"
      >
        <DispatchDetailBody v-if="dispatchData" :data="dispatchData" />
      </EntityDetailDrawer>
    </template>

    <AiAssistantPanel
      v-if="authStore.isDispatcher"
      :schedules="schedules"
      :selected-schedule-code="selectedCode"
      @draft-created="onAiDraftCreated"
    />
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

.draft-alert {
  margin-bottom: 16px;
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
