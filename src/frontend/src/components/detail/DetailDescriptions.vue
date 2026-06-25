<script setup lang="ts">
defineProps<{
  column?: number
}>()
</script>

<template>
  <el-descriptions
    :column="column ?? 1"
    border
    size="small"
    class="detail-descriptions"
  >
    <slot />
  </el-descriptions>
</template>

<style scoped>
.detail-descriptions {
  margin-bottom: var(--section-gap, 12px);
}

.detail-descriptions :deep(.el-descriptions__label) {
  width: var(--detail-label-width, 120px);
}
</style>
