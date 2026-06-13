<script setup lang="ts">
defineProps<{
  title?: string
}>()
</script>

<template>
  <div class="page-toolbar">
    <div v-if="title" class="page-toolbar-title">{{ title }}</div>
    <div class="page-toolbar-filters">
      <slot name="filters" />
    </div>
    <div class="page-toolbar-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.page-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.page-toolbar-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-right: auto;
}

.page-toolbar-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.page-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
</style>
