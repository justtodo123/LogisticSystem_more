<script setup lang="ts">
import type { GlobalScheduleSummary } from '@/types/schedule'

defineProps<{
  summary: GlobalScheduleSummary | null
  loading?: boolean
}>()
</script>

<template>
  <el-row v-loading="loading" :gutter="16" class="summary-row">
    <el-col :xs="12" :sm="6">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">总距离 (km)</div>
        <div class="summary-value">
          {{ summary?.total_distance?.toFixed(1) ?? '—' }}
        </div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">总时间 (小时)</div>
        <div class="summary-value">
          {{ summary?.total_time?.toFixed(0) ?? '—' }}
        </div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">货物数</div>
        <div class="summary-value">{{ summary?.total_goods ?? '—' }}</div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">评分（越低越好）</div>
        <div class="summary-value">
          {{ summary?.score?.toFixed(1) ?? '—' }}
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.summary-row {
  margin-bottom: 0;
}

.summary-card {
  text-align: center;
}

.summary-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}
</style>
