<script setup lang="ts">
defineProps<{
  modelValue: boolean
  title?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function onClose(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    :title="title ?? '详情'"
    size="480px"
    destroy-on-close
    class="entity-detail-drawer"
    @update:model-value="emit('update:modelValue', $event)"
    @close="onClose"
  >
    <div
      v-loading="loading"
      element-loading-text="加载详情中…"
      class="entity-detail-body"
    >
      <slot />
      <el-empty
        v-if="!loading && !$slots.default"
        class="detail-empty"
        description="暂无数据"
        :image-size="64"
      />
    </div>
  </el-drawer>
</template>

<style scoped>
.entity-detail-body {
  min-height: 120px;
  padding: 0 4px 8px;
}
</style>
