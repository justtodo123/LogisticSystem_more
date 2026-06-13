<script setup lang="ts">
defineProps<{
  loading?: boolean
}>()
</script>

<template>
  <div v-loading="loading" class="data-table-wrap">
    <el-table v-bind="$attrs">
      <slot />
    </el-table>
  </div>
</template>

<style scoped>
.data-table-wrap {
  min-height: 200px;
}
</style>
