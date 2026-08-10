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

/** T2-3 多目标分项评分（来自 explanation.score_breakdown，列表形式） */
const breakdownItems = computed(() => {
  const s = props.summary
  const items = s?.explanation?.score_breakdown ?? []
  if (items.length) return items
  // 兼容旧字段（前端曾经期望的单目标拆解对象）
  const legacy = s?.score_breakdown
  if (legacy) {
    return [
      { objective: '距离', weight: 0, direction: 'minimize' as const, score: legacy.distance_component },
      { objective: '时间', weight: 0, direction: 'minimize' as const, score: legacy.time_component },
      { objective: '货物', weight: 0, direction: 'minimize' as const, score: legacy.goods_component },
    ]
  }
  return []
})

const constraints = computed(() => props.summary?.explanation?.constraints_hit ?? [])

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

function objectiveLabel(obj: string): string {
  const map: Record<string, string> = {
    distance: '距离',
    time: '时间',
    load_rate: '满载率',
    on_time_rate: '时效',
    cost: '成本',
  }
  return map[obj] ?? obj
}
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

    <!-- T2-3 评分拆解与约束命中 -->
    <el-collapse v-if="summary && (breakdownItems.length || constraints.length)" class="explain-collapse">
      <el-collapse-item
        title="评分拆解与约束分析"
        name="explain"
      >
        <div v-if="summary.explanation?.summary" class="explain-summary">
          {{ summary.explanation.summary }}
        </div>
        <div v-if="breakdownItems.length" class="explain-grid">
          <div
            v-for="item in breakdownItems"
            :key="item.objective"
            class="explain-item"
          >
            <span class="explain-item-label">
              {{ objectiveLabel(item.objective) }}
              <el-tag v-if="item.weight" size="small" type="info">
                w{{ (item.weight * 100).toFixed(0) }}%
              </el-tag>
            </span>
            <span class="explain-item-score">
              {{ item.score != null ? (item.score * 100).toFixed(0) + '分' : '—' }}
            </span>
            <span v-if="item.raw != null" class="explain-item-raw">
              原始 {{ item.raw.toFixed(1) }}
            </span>
          </div>
        </div>
        <ul v-if="constraints.length" class="explain-constraints">
          <li
            v-for="(c, i) in constraints"
            :key="i"
            :class="['explain-constraint', `is-${c.severity}`]"
          >
            <el-tag :type="c.severity === 'warning' ? 'warning' : 'success'" size="small">
              {{ c.name }}
            </el-tag>
            <span>{{ c.detail }}</span>
          </li>
        </ul>
      </el-collapse-item>
    </el-collapse>
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

.explain-collapse {
  margin-top: 12px;
  border: 1px solid var(--border-color-lighter, #ebeef5);
  border-radius: var(--card-radius, 6px);
}

.explain-summary {
  font-size: 13px;
  color: var(--text-regular, #606266);
  margin-bottom: 10px;
}

.explain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.explain-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: var(--fill-color-light, #f5f7fa);
  border-radius: 4px;
}

.explain-item-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-regular, #606266);
}

.explain-item-score {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.explain-item-raw {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.explain-constraints {
  list-style: none;
  margin: 0;
  padding: 0;
}

.explain-constraint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
  color: var(--text-regular, #606266);
}

.explain-constraint.is-warning {
  color: var(--el-color-warning, #e6a23c);
}
</style>
