<script setup lang="ts">
import { computed } from 'vue'
import type { GlobalScheduleSummary } from '@/types/schedule'

const props = defineProps<{
  summary: GlobalScheduleSummary | null
  loading?: boolean
  isDraft?: boolean
}>()

const usesDisplayScore = computed(
  () => props.summary?.score_display != null,
)

const scoreLabel = computed(() =>
  usesDisplayScore.value ? '综合评分（越高越好）' : '评分（越低越好）',
)

const displayScore = computed(() => {
  if (!props.summary) return null
  const raw = props.summary.score_display ?? props.summary.score
  return typeof raw === 'number' ? raw.toFixed(1) : '—'
})

const tooltipContent = computed(() => {
  const s = props.summary
  if (!s) return ''
  const lines: string[] = []
  const b = s.score_breakdown

  if (s.score_display != null) {
    lines.push(`归一化评分：${s.score_display}（越高越好）`)
    lines.push(`原始加权分：${s.score.toFixed(1)}（越低越好）`)
  } else {
    lines.push('综合评分，越低越好')
  }

  if (b) {
    lines.push(
      `距离分项：${b.distance_component.toFixed(1)}`,
      `时间分项：${b.time_component.toFixed(1)}`,
      `货物分项：${b.goods_component.toFixed(1)}`,
    )
    if (b.formula) lines.push(b.formula)
  }

  return lines.join('\n')
})
</script>

<template>
  <div v-loading="loading" class="summary-wrap">
    <div
      v-if="summary && (summary.version != null || summary.is_replan)"
      class="summary-meta"
    >
      <span v-if="summary.version != null" class="summary-version">
        版本 v{{ summary.version }}
      </span>
      <el-tag v-if="summary.is_replan" type="warning" size="small">重规划</el-tag>
      <el-tag v-if="isDraft || summary.status === 'draft'" type="warning" size="small">
        预览
      </el-tag>
    </div>
    <el-row :gutter="16" class="summary-row">
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
        <div class="summary-label">{{ scoreLabel }}</div>
        <el-tooltip
          v-if="summary"
          :content="tooltipContent"
          placement="top"
          effect="dark"
        >
          <div class="summary-value summary-score">
            {{ displayScore }}
          </div>
        </el-tooltip>
        <div v-else class="summary-value">—</div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">包裹数</div>
        <div class="summary-value">{{ summary?.package_count ?? '—' }}</div>
      </el-card>
    </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.summary-wrap {
  margin-bottom: 0;
}

.summary-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--section-gap, 12px);
}

.summary-version {
  font-size: 14px;
  color: var(--text-regular, #606266);
}

.summary-row {
  margin-bottom: 0;
}

.summary-card {
  text-align: center;
  border-radius: var(--card-radius, 6px);
}

.summary-label {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  margin-bottom: 8px;
}

.summary-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.summary-score {
  cursor: help;
  display: inline-block;
}
</style>
