<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DispatchBatchDetail, NodeDispatchItem } from '@/types/dispatch'
import { formatNodeWithName } from '@/utils/schedule-format'

const props = defineProps<{
  detail: DispatchBatchDetail | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'open-dispatch': [item: NodeDispatchItem]
}>()

const keyword = ref('')

interface PhaseGroup {
  level_phase: 0 | 1
  rows: NodeDispatchItem[]
}

function matchesKeyword(row: NodeDispatchItem, q: string): boolean {
  if (
    row.dispatch_code.toLowerCase().includes(q) ||
    row.vehicle_code.toLowerCase().includes(q) ||
    (row.driver_code?.toLowerCase().includes(q) ?? false)
  ) {
    return true
  }
  return row.tasks.some((t) => {
    if (t.is_return) return false
    const pathText = `${t.from_node_code} ${t.to_node_code} ${t.from_node_name ?? ''} ${t.to_node_name ?? ''}`.toLowerCase()
    return (
      pathText.includes(q) ||
      t.package_codes.some((c) => c.toLowerCase().includes(q))
    )
  })
}

const phaseGroups = computed<PhaseGroup[]>(() => {
  const items = props.detail?.dispatches ?? []
  const q = keyword.value.trim().toLowerCase()
  const filtered = q ? items.filter((row) => matchesKeyword(row, q)) : items
  const groups: PhaseGroup[] = []
  for (const phase of [0, 1] as const) {
    const rows = filtered.filter((d) => d.level_phase === phase)
    if (rows.length > 0) {
      groups.push({ level_phase: phase, rows })
    }
  }
  return groups
})

const hasAnyRows = computed(
  () => (props.detail?.dispatches?.length ?? 0) > 0,
)

function phaseLabel(level: 0 | 1): string {
  return level === 0 ? 'L0 → L1' : 'L1 → L2'
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
      <div class="vehicle-header">
        <span>车辆任务</span>
        <el-input
          v-if="hasAnyRows"
          v-model="keyword"
          placeholder="搜索调度/车辆/包裹/节点"
          clearable
          size="small"
          class="vehicle-search"
        />
      </div>
    </template>
    <el-empty
      v-if="!loading && !hasAnyRows"
      description="请选择调度批次查看车辆任务"
    />
    <el-empty
      v-else-if="!loading && hasAnyRows && !phaseGroups.length"
      description="无匹配的车辆任务"
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
              <el-table-column label="路线" min-width="200" show-overflow-tooltip>
                <template #default="{ row: task }">
                  {{
                    formatNodeWithName(task.from_node_code, task.from_node_name)
                  }}
                  →
                  {{ formatNodeWithName(task.to_node_code, task.to_node_name) }}
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
        <el-table-column prop="dispatch_code" label="调度编号" min-width="140">
          <template #default="{ row }">
            <el-link
              type="primary"
              :underline="false"
              @click="emit('open-dispatch', row)"
            >
              {{ row.dispatch_code }}
            </el-link>
          </template>
        </el-table-column>
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

.vehicle-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.vehicle-search {
  max-width: 260px;
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
