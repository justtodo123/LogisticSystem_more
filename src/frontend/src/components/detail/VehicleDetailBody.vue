<script setup lang="ts">
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import { VEHICLE_STATUS_MAP } from '@/constants/status'
import type { VehicleDetail, VehicleStatus } from '@/types/vehicle'
import { formatDateTime } from '@/utils/format'

defineProps<{
  data: VehicleDetail
}>()

function statusLabel(status: VehicleStatus): string {
  return VEHICLE_STATUS_MAP[status]?.label ?? status
}
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="车牌号">{{ data.vehicle_code }}</el-descriptions-item>
    <el-descriptions-item label="车型">{{ data.model }}</el-descriptions-item>
    <el-descriptions-item label="载重">{{ data.capacity }} t</el-descriptions-item>
    <el-descriptions-item label="能源">{{ data.energy_type }}</el-descriptions-item>
    <el-descriptions-item label="车辆类型">{{ data.vehicle_type }}</el-descriptions-item>
    <el-descriptions-item label="状态">{{ statusLabel(data.status) }}</el-descriptions-item>
    <el-descriptions-item label="所属节点">
      {{ data.node_name || data.node_code }}
      <span class="detail-sub">（{{ data.node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item label="最后到达">
      {{ data.last_arrived_node_name || data.last_arrived_node_code }}
      <span class="detail-sub">（{{ data.last_arrived_node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item v-if="data.capability_tags?.length" label="能力标签">
      {{ data.capability_tags.join('、') }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.created_at" label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.updated_at" label="更新时间">
      {{ formatDateTime(data.updated_at) }}
    </el-descriptions-item>
  </DetailDescriptions>
</template>
