<script setup lang="ts">
import { computed } from 'vue'
import type { DispatchBatchDetail, NodeDispatchPhase } from '@/types/dispatch'

const props = defineProps<{
  detail: DispatchBatchDetail | null
  loading?: boolean
}>()

const phases = computed<NodeDispatchPhase[]>(() => props.detail?.dispatches ?? [])

function phaseLabel(level: 0 | 1): string {
  return level === 0 ? 'L0 → L1' : 'L1 → L2'
}

function formatPath(from: string, to: string): string {
  return `${from} → ${to}`
}

function formatPackages(codes: string[]): string {
  return codes.length ? codes.join(', ') : '—'
}
</script>

<template>
  <el-card shadow="never" class="vehicle-panel">
    <template #header>
      <span>车辆任务</span>
    </template>
    <el-empty
      v-if="!loading && !phases.length"
      description="请选择调度批次查看车辆任务"
    />
    <div v-for="phase in phases" :key="phase.dispatch_code" class="phase-block">
      <div class="phase-title">
        <el-tag type="primary" size="small">{{ phaseLabel(phase.level_phase) }}</el-tag>
        <span class="phase-code">{{ phase.dispatch_code }}</span>
      </div>
      <el-table
        v-loading="loading"
        :data="phase.vehicle_tasks"
        stripe
        border
        size="small"
        row-key="vehicle_code"
        empty-text="该阶段暂无车辆任务"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <el-table :data="row.tasks" size="small" border>
              <el-table-column label="路线" min-width="160">
                <template #default="{ row: task }">
                  {{ formatPath(task.from_node_code, task.to_node_code) }}
                </template>
              </el-table-column>
              <el-table-column label="包裹" min-width="200" show-overflow-tooltip>
                <template #default="{ row: task }">
                  {{ formatPackages(task.package_codes) }}
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-table-column>
        <el-table-column prop="vehicle_code" label="车辆编号" min-width="120" />
        <el-table-column prop="driver_code" label="司机编号" min-width="120" />
        <el-table-column prop="distance" label="距离 (km)" min-width="100">
          <template #default="{ row }">
            {{ row.distance?.toFixed(1) ?? '—' }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<style scoped>
.vehicle-panel {
  margin-top: 0;
}

.phase-block + .phase-block {
  margin-top: 20px;
}

.phase-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.phase-code {
  font-size: 13px;
  color: #909399;
}
</style>
