<script setup lang="ts">
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import { DRIVER_STATUS_MAP } from '@/constants/status'
import type { DriverDetail, DriverStatus } from '@/types/driver'
import { formatDateTime } from '@/utils/format'

defineProps<{
  data: DriverDetail
}>()

function statusLabel(status: DriverStatus): string {
  return DRIVER_STATUS_MAP[status]?.label ?? status
}
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="司机编号">{{ data.driver_code }}</el-descriptions-item>
    <el-descriptions-item label="姓名">{{ data.name }}</el-descriptions-item>
    <el-descriptions-item label="电话">{{ data.phone }}</el-descriptions-item>
    <el-descriptions-item label="驾照类型">{{ data.license_type }}</el-descriptions-item>
    <el-descriptions-item label="班次">{{ data.shift }}</el-descriptions-item>
    <el-descriptions-item label="所属节点">
      {{ data.node_name || data.node_code }}
      <span class="detail-sub">（{{ data.node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item label="状态">{{ statusLabel(data.status) }}</el-descriptions-item>
    <el-descriptions-item v-if="data.created_at" label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.updated_at" label="更新时间">
      {{ formatDateTime(data.updated_at) }}
    </el-descriptions-item>
  </DetailDescriptions>
</template>
