<script setup lang="ts">
import { computed } from 'vue'
import type { SlaReport } from '@/types/report'

const props = defineProps<{
  sla: SlaReport | null
  loading?: boolean
}>()

/** 准点率转为百分比 */
const ratePercent = computed(() => {
  if (!props.sla) return 0
  return Math.round(props.sla.on_time_rate * 1000) / 10
})

/** 依据准点率分档着色：≥90% 绿，≥60% 橙，否则红 */
const rateColor = computed(() => {
  const p = ratePercent.value
  if (p >= 90) return '#67c23a'
  if (p >= 60) return '#e6a23c'
  return '#f56c6c'
})

/** 平均延迟：分钟 → 可读时长 */
const avgDelayText = computed(() => {
  if (props.sla == null) return '--'
  const m = Math.round(props.sla.avg_delay_minutes)
  if (m <= 0) return '0 分钟'
  if (m < 60) return `${m} 分钟`
  const h = m / 60
  if (h < 24) return `${Math.round(h * 10) / 10} 小时`
  return `${Math.round((h / 24) * 10) / 10} 天`
})
</script>

<template>
  <div class="sla-gauge" :class="{ 'is-loading': loading }">
    <el-progress
      v-if="sla"
      type="dashboard"
      :percentage="ratePercent"
      :width="180"
      :stroke-width="12"
      :color="rateColor"
    >
      <template #default>
        <div class="gauge-center">
          <div class="gauge-rate" :style="{ color: rateColor }">
            {{ ratePercent.toFixed(1) }}%
          </div>
          <div class="gauge-label">准点率</div>
        </div>
      </template>
    </el-progress>
    <el-skeleton v-else animated>
      <template #template>
        <div class="gauge-skeleton" />
      </template>
    </el-skeleton>

    <div class="sla-metrics">
      <div class="metric">
        <span class="metric-label">SLA 目标</span>
        <span class="metric-value">{{ sla?.sla_target_hours ?? '--' }} 小时</span>
      </div>
      <div class="metric">
        <span class="metric-label">平均延迟</span>
        <span class="metric-value">{{ avgDelayText }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">已签收</span>
        <span class="metric-value">
          {{ sla?.signed_orders ?? '--' }} / {{ sla?.total_orders ?? '--' }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sla-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gauge-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.gauge-rate {
  font-size: 26px;
  font-weight: 700;
}

.gauge-label {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

.gauge-skeleton {
  width: 180px;
  height: 180px;
  border-radius: 50%;
}

.sla-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  width: 100%;
  margin-top: 20px;
  padding: 12px 0;
  border-top: 1px dashed var(--meta-border, #ebeef5);
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.metric-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}
</style>
