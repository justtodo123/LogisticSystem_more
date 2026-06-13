<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import GoodsPathTable from '@/components/schedule/GoodsPathTable.vue'
import ScheduleSummaryCards from '@/components/schedule/ScheduleSummaryCards.vue'
import { useGlobalSchedule } from '@/composables/useGlobalSchedule'

const authStore = useAuthStore()

const {
  schedules,
  selectedCode,
  summary,
  detail,
  listLoading,
  detailLoading,
  generating,
  loadSchedules,
  generateSchedule,
} = useGlobalSchedule()

onMounted(() => {
  void loadSchedules()
})
</script>

<template>
  <div class="dashboard page-card">
    <div class="dashboard-header">
      <div>
        <h2 class="dashboard-title">调度工作台</h2>
        <p class="dashboard-desc">
          欢迎，{{ authStore.displayName }}（{{ authStore.role }}）
        </p>
      </div>
      <div class="dashboard-toolbar">
        <el-button
          v-if="authStore.isDispatcher"
          type="primary"
          :loading="generating"
          :disabled="generating"
          @click="generateSchedule"
        >
          生成全局调度
        </el-button>
        <el-tag v-else type="info">只读模式</el-tag>
        <el-select
          v-model="selectedCode"
          placeholder="选择历史方案"
          clearable
          filterable
          :loading="listLoading"
          style="width: 240px"
          :disabled="!schedules.length"
        >
          <el-option
            v-for="item in schedules"
            :key="item.schedule_code"
            :label="`${item.schedule_code}（${item.created_at ?? ''}）`"
            :value="item.schedule_code"
          />
        </el-select>
      </div>
    </div>

    <el-empty
      v-if="!listLoading && !schedules.length"
      description="暂无调度方案，请先生成全局调度"
    />

    <template v-else>
      <ScheduleSummaryCards
        :summary="summary"
        :loading="detailLoading && !summary"
      />
      <div class="dashboard-body">
        <GoodsPathTable
          :items="detail?.goods_schedules ?? []"
          :loading="detailLoading"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.dashboard-title {
  margin: 0 0 8px;
  font-size: 20px;
}

.dashboard-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.dashboard-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.dashboard-body {
  margin-top: 20px;
}
</style>
