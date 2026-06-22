<script setup lang="ts">
import { computed } from 'vue'
import type { DispatchBatchSummary } from '@/types/dispatch'
import type { BatchStatus } from '@/types/dispatch'

const props = defineProps<{
  batches: DispatchBatchSummary[]
  selectedBatchCode: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:selectedBatchCode': [value: string]
}>()

const current = computed(() =>
  props.batches.find((b) => b.batch_code === props.selectedBatchCode) ?? null,
)

const STATUS_LABEL: Record<BatchStatus, string> = {
  pending: '待执行',
  l0_l1_done: 'L0→L1 完成',
  completed: '已完成',
  failed: '失败',
}

const STATUS_TYPE: Record<BatchStatus, 'info' | 'warning' | 'success' | 'danger'> = {
  pending: 'info',
  l0_l1_done: 'warning',
  completed: 'success',
  failed: 'danger',
}
</script>

<template>
  <el-card shadow="never" class="batch-panel">
    <template #header>
      <span>调度批次</span>
    </template>
    <el-empty
      v-if="!loading && !batches.length"
      description="暂无节点间调度批次，请先生成"
    />
    <template v-else>
      <el-select
        :model-value="selectedBatchCode"
        placeholder="选择调度批次"
        filterable
        clearable
        :loading="loading"
        style="width: 100%; margin-bottom: 12px"
        @update:model-value="emit('update:selectedBatchCode', $event)"
      >
        <el-option
          v-for="item in batches"
          :key="item.batch_code"
          :label="`${item.batch_code}（${item.vehicle_count} 辆车）`"
          :value="item.batch_code"
        />
      </el-select>
      <el-descriptions v-if="current" :column="2" border size="small">
        <el-descriptions-item label="批次编号">{{ current.batch_code }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="STATUS_TYPE[current.status]" size="small">
            {{ STATUS_LABEL[current.status] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="车辆数">{{ current.vehicle_count }}</el-descriptions-item>
        <el-descriptions-item v-if="current.l0_l1_dispatch_count != null" label="L0→L1 车辆">
          {{ current.l0_l1_dispatch_count }}
        </el-descriptions-item>
        <el-descriptions-item v-if="current.l1_l2_dispatch_count != null" label="L1→L2 车辆">
          {{ current.l1_l2_dispatch_count }}
        </el-descriptions-item>
      </el-descriptions>
    </template>
  </el-card>
</template>

<style scoped>
.batch-panel {
  margin-bottom: 16px;
}
</style>
