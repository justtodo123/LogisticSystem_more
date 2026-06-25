<script setup lang="ts">
defineProps<{
  loading?: boolean
}>()
</script>

<template>
  <div v-loading="loading" class="data-table-wrap">
    <el-table stripe v-bind="$attrs">
      <slot />
    </el-table>
  </div>
</template>

<style scoped>
.data-table-wrap {
  min-height: 200px;
}

.data-table-wrap :deep(.el-table) {
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
}

.data-table-wrap :deep(.el-table th.el-table__cell) {
  font-weight: 600;
  color: var(--text-primary, #303133);
  background-color: var(--meta-bg, #f5f7fa);
}

.data-table-wrap :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: var(--layout-sidebar-hover-bg, #409eff10);
}
</style>
