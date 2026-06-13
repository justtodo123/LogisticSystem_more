<script setup lang="ts">
import type { GoodsScheduleItem } from '@/types/schedule'

defineProps<{
  items: GoodsScheduleItem[]
  loading?: boolean
}>()

function formatPath(path: string[]): string {
  return path.length ? path.join(' → ') : '—'
}
</script>

<template>
  <el-card shadow="never" class="path-panel">
    <template #header>
      <span>货物路径</span>
    </template>
    <el-table
      v-loading="loading"
      :data="items"
      stripe
      border
      size="small"
      empty-text="请选择调度方案或先生成全局调度"
    >
      <el-table-column prop="goods_code" label="货物编号" min-width="120" />
      <el-table-column prop="order_code" label="订单编号" min-width="120" />
      <el-table-column label="路径" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ formatPath(row.path) }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.path-panel {
  height: 100%;
}
</style>
