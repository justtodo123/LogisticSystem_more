<script setup lang="ts">
import type { NodeDispatchItem } from '@/types/dispatch'
import { formatNodeWithName } from '@/utils/schedule-format'

defineProps<{
  data: NodeDispatchItem
}>()

function formatPackages(codes: string[]): string {
  return codes.length ? codes.join(', ') : '—'
}
</script>

<template>
  <div class="dispatch-detail-body">
    <el-descriptions :column="1" border size="small">
      <el-descriptions-item label="调度编号">
        {{ data.dispatch_code }}
      </el-descriptions-item>
      <el-descriptions-item label="车辆编号">
        {{ data.vehicle_code }}
      </el-descriptions-item>
      <el-descriptions-item label="司机编号">
        {{ data.driver_code ?? '—' }}
      </el-descriptions-item>
      <el-descriptions-item label="阶段">
        {{ data.level_phase === 0 ? 'L0 → L1' : 'L1 → L2' }}
      </el-descriptions-item>
      <el-descriptions-item label="总距离">
        {{ data.total_distance?.toFixed(1) ?? '—' }} km
      </el-descriptions-item>
    </el-descriptions>

    <div class="detail-section-title">运输任务</div>
    <el-table
      :data="data.tasks.filter((t) => !t.is_return)"
      size="small"
      border
      stripe
    >
      <el-table-column label="路线" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{
            formatNodeWithName(row.from_node_code, row.from_node_name)
          }}
          →
          {{ formatNodeWithName(row.to_node_code, row.to_node_name) }}
        </template>
      </el-table-column>
      <el-table-column label="包裹" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          {{ formatPackages(row.package_codes) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.dispatch-detail-body {
  padding: 0 4px;
}
</style>
