<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div class="dashboard">
    <h2>调度工作台</h2>
    <p class="dashboard-desc">
      欢迎，{{ authStore.displayName }}（{{ authStore.role }}）
    </p>
    <p class="dashboard-hint">基础数据管理请从侧栏进入；全局调度将在阶段 3 接入。</p>

    <div class="dashboard-actions">
      <el-button v-if="authStore.isDispatcher" type="primary">新增</el-button>
      <el-button v-if="authStore.isDispatcher" type="danger">删除</el-button>
      <el-tag v-else type="info">只读模式：写操作已隐藏</el-tag>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 720px;
}

.dashboard-desc {
  margin: 12px 0;
  color: #606266;
}

.dashboard-hint {
  margin: 0 0 24px;
  color: #909399;
  font-size: 14px;
}

.dashboard-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>
