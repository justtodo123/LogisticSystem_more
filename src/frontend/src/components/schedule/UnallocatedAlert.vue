<script setup lang="ts">
import { useRouter } from 'vue-router'
import { goToPackages } from '@/utils/detail-navigation'

defineProps<{
  codes?: string[]
}>()

const router = useRouter()
</script>

<template>
  <el-alert
    v-if="codes?.length"
    type="warning"
    :closable="false"
    show-icon
    class="unallocated-alert enhance-panel"
    title="存在未分配包裹"
  >
    <template #default>
      <p class="alert-desc">
        以下 {{ codes.length }} 个包裹未能分配到车辆任务，请检查运力或重新调度：
      </p>
      <div class="code-list">
        <el-link
          v-for="code in codes"
          :key="code"
          type="warning"
          :underline="false"
          class="code-link"
          @click="goToPackages(router, { package_code: code })"
        >
          {{ code }}
        </el-link>
      </div>
    </template>
  </el-alert>
</template>

<style scoped>
.alert-desc {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--text-regular, #606266);
}

.code-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.code-link {
  font-size: 13px;
}
</style>
