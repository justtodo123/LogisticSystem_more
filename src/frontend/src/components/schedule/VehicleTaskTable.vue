<script setup lang="ts">
import { computed } from 'vue'
import type { DispatchBatchDetail, NodeDispatchItem } from '@/types/dispatch'

const props = defineProps<{
  detail: DispatchBatchDetail | null
  loading?: boolean
}>()

interface PhaseGroup {
  level_phase: 0 | 1
  rows: NodeDispatchItem[]
}

const phaseGroups = computed<PhaseGroup[]>(() => {
  const items = props.detail?.dispatches ?? []
  const groups: PhaseGroup[] = []
  for (const phase of [0, 1] as const) {
    const rows = items.filter((d) => d.level_phase === phase)
    if (rows.length > 0) {
      groups.push({ level_phase: phase, rows })
    }
  }
  return groups
})

function phaseLabel(level: 0 | 1): string {
  return level === 0 ? 'L0 → L1' : 'L1 → L2'
}

function formatPath(from: string, to: string): string {
  return `${from} → ${to}`
}

function formatPackages(codes: string[]): string {
  return codes.length ? codes.join(', ') : '—'
}

function nonReturnTasks(tasks: NodeDispatchItem['tasks']) {
  return tasks.filter((t) => !t.is_return)
}
</script>

<template>
  <el-card shadow="never" class="vehicle-panel">
    <template #header>
      <span>车辆任务</span>
    </template>
    <el-empty
      v-if="!loading && !phaseGroups.length"
      description="请选择调度批次查看车辆任务"
    />
    <div v-for="group in phaseGroups" :key="group.level_phase" class="phase-block">
      <div class="phase-title">
        <el-tag type="primary" size="small">{{ phaseLabel(group.level_phase) }}</el-tag>
        <span class="phase-code">{{ group.rows.length }} 辆车</span>
      </div>
      <el-table
        v-loading="loading"
        :data="group.rows"
        stripe
        border
        size="small"
        row-key="dispatch_code"
        empty-text="该阶段暂无车辆任务"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <el-table :data="nonReturnTasks(row.tasks)" size="small" border>
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
        <el-table-column prop="dispatch_code" label="调度编号" min-width="140" />
        <el-table-column prop="vehicle_code" label="车辆编号" min-width="120" />
        <el-table-column prop="driver_code" label="司机编号" min-width="120" />
        <el-table-column label="距离 (km)" min-width="100">
          <template #default="{ row }">
            {{ row.total_distance?.toFixed(1) ?? '—' }}
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
