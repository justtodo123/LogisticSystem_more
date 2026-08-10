<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { DispatchBatchDetail, NodeDispatchItem } from '@/types/dispatch'
import { formatNodeWithName } from '@/utils/schedule-format'
import { listDrivers } from '@/api/drivers'
import { listVehicles } from '@/api/vehicles'
import {
  overrideDispatchDriver,
  overrideDispatchVehicle,
  undoDispatchOverride,
} from '@/api/schedule'

const props = defineProps<{
  detail: DispatchBatchDetail | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'open-dispatch': [item: NodeDispatchItem]
  'refresh': []
}>()

const keyword = ref('')

// ── T2-4 人工干预：换车/换司机对话框 ──
const overrideVisible = ref(false)
const overrideKind = ref<'vehicle' | 'driver'>('vehicle')
const overrideDispatch = ref<string | null>(null)
const candidateOptions = ref<Array<{ value: string; label: string }>>([])
const candidateLoading = ref(false)
const targetCode = ref('')

/** 批次处于可执行前（pending/l0_l1_done/未知）时允许人工干预 */
const canIntervene = computed(() => {
  const s = props.detail?.status
  return s == null || s === 'pending' || s === 'l0_l1_done'
})

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

// ── T2-4 人工干预操作 ──
async function openOverride(row: NodeDispatchItem, kind: 'vehicle' | 'driver'): Promise<void> {
  overrideKind.value = kind
  overrideDispatch.value = row.dispatch_code
  targetCode.value = ''
  overrideVisible.value = true
  candidateLoading.value = true
  try {
    if (kind === 'vehicle') {
      const res = await listVehicles({ page: 1, page_size: 200 })
      candidateOptions.value = res.items.map((v) => ({
        value: v.vehicle_code,
        label: `${v.vehicle_code}（${v.model}）`,
      }))
    } else {
      const res = await listDrivers({ page: 1, page_size: 200 })
      candidateOptions.value = res.items.map((d) => ({
        value: d.driver_code,
        label: `${d.driver_code}（${d.name}）`,
      }))
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载候选列表失败')
  } finally {
    candidateLoading.value = false
  }
}

async function applyOverride(): Promise<void> {
  if (!overrideDispatch.value || !targetCode.value) {
    ElMessage.warning('请选择目标' + (overrideKind.value === 'vehicle' ? '车辆' : '司机'))
    return
  }
  try {
    const result =
      overrideKind.value === 'vehicle'
        ? await overrideDispatchVehicle(overrideDispatch.value, targetCode.value)
        : await overrideDispatchDriver(overrideDispatch.value, targetCode.value)
    overrideVisible.value = false
    ElMessage.success(
      `干预成功：${result.vehicle_code ?? result.driver_code}（版本 v${result.version}）`,
    )
    emit('refresh')
  } catch (err) {
    // 后端校验拒绝时 message 即拒绝原因
    ElMessage.error(err instanceof Error ? err.message : '人工干预失败')
  }
}

async function handleUndo(row: NodeDispatchItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确认撤销「${row.dispatch_code}」的人工干预？将恢复到调整前的车辆/司机。`,
      '撤销干预',
      { type: 'warning', confirmButtonText: '撤销', cancelButtonText: '取消' },
    )
  } catch {
    return // cancelled
  }
  try {
    const result = await undoDispatchOverride(row.dispatch_code)
    ElMessage.success(
      `已撤销，恢复车辆 ${result.vehicle_code ?? '—'} / 司机 ${result.driver_code ?? '—'}（版本 v${result.version}）`,
    )
    emit('refresh')
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '撤销失败')
  }
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
        <el-table-column prop="driver_code" label="司机编号" min-width="120">
          <template #default="{ row }">
            {{ row.driver_code ?? '—' }}
            <el-tag v-if="row.can_undo" type="warning" size="small" class="overridden-tag">
              已干预
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="距离 (km)" min-width="100">
          <template #default="{ row }">
            {{ row.total_distance?.toFixed(1) ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column v-if="canIntervene"
          label="干预" min-width="180" fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="openOverride(row, 'vehicle')"
            >
              换车
            </el-button>
            <el-button
              link
              type="primary"
              size="small"
              @click="openOverride(row, 'driver')"
            >
              换司机
            </el-button>
            <el-button
              v-if="row.can_undo"
              link
              type="danger"
              size="small"
              @click="handleUndo(row)"
            >
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- T2-4 换车/换司机对话框 -->
    <el-dialog
      v-model="overrideVisible"
      :title="overrideKind === 'vehicle' ? '更换车辆' : '更换司机'"
      width="420px"
      destroy-on-close
    >
      <div class="override-dialog-body">
        <div class="override-target">调度明细：{{ overrideDispatch }}</div>
        <el-select
          v-model="targetCode"
          filterable
          :loading="candidateLoading"
          :placeholder="overrideKind === 'vehicle' ? '选择目标车辆' : '选择目标司机'"
          class="override-select"
        >
          <el-option
            v-for="opt in candidateOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <div class="override-hint">
          系统将自动校验
          {{ overrideKind === 'vehicle' ? '容量 / 时窗 / 路径数' : '驾时 / 排班 / 节点' }}
          约束，不满足时拒绝并提示原因。
        </div>
      </div>
      <template #footer>
        <el-button @click="overrideVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!targetCode" @click="applyOverride">
          确认更换
        </el-button>
      </template>
    </el-dialog>
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

.overridden-tag {
  margin-left: 4px;
}

.override-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.override-target {
  font-size: 13px;
  color: #606266;
}

.override-select {
  width: 100%;
}

.override-hint {
  font-size: 12px;
  color: #909399;
}
</style>
