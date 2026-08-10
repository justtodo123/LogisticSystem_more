<script setup lang="ts">
import { computed } from 'vue'
import type { ExceptionCountItem } from '@/types/report'

const props = defineProps<{
  byType: ExceptionCountItem[]
  loading?: boolean
}>()

const PALETTE = [
  '#409eff',
  '#67c23a',
  '#e6a23c',
  '#f56c6c',
  '#909399',
  '#9c6cf5',
  '#36cfc9',
  '#ff7a45',
]

interface Segment {
  label: string
  value: number
  color: string
  dash: string
  offset: number
}

const RADIUS = 70
const STROKE_WIDTH = 26
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

const segments = computed<Segment[]>(() => {
  const total = props.byType.reduce((sum, s) => sum + s.count, 0)
  let accumulated = 0
  return props.byType.map((item, index) => {
    const frac = total > 0 ? item.count / total : 0
    const len = frac * CIRCUMFERENCE
    const seg: Segment = {
      label: item.type || '未知',
      value: item.count,
      color: PALETTE[index % PALETTE.length],
      dash: `${len} ${CIRCUMFERENCE - len}`,
      offset: -accumulated,
    }
    accumulated += len
    return seg
  })
})

const totalCount = computed(() =>
  props.byType.reduce((sum, s) => sum + s.count, 0),
)

const empty = computed(() => !props.byType.length && !props.loading)
</script>

<template>
  <div class="exception-pie">
    <el-skeleton v-if="loading" animated>
      <template #template>
        <div class="pie-skeleton" />
      </template>
    </el-skeleton>

    <el-empty v-else-if="empty" description="暂无异常数据" :image-size="72" />

    <div v-else class="pie-body">
      <svg
        class="pie-svg"
        :viewBox="`0 0 ${RADIUS * 2 + STROKE_WIDTH + 4} ${RADIUS * 2 + STROKE_WIDTH + 4}`"
        role="img"
        aria-label="异常类型分布"
      >
        <g
          :transform="`rotate(-90 ${RADIUS + STROKE_WIDTH / 2 + 2} ${RADIUS + STROKE_WIDTH / 2 + 2})`"
        >
          <circle
            v-for="(seg, index) in segments"
            :key="`${seg.label}-${index}`"
            :cx="RADIUS + STROKE_WIDTH / 2 + 2"
            :cy="RADIUS + STROKE_WIDTH / 2 + 2"
            :r="RADIUS"
            fill="none"
            :stroke="seg.color"
            :stroke-width="STROKE_WIDTH"
            :stroke-dasharray="seg.dash"
            :stroke-dashoffset="seg.offset"
          />
        </g>
        <text
          :x="RADIUS + STROKE_WIDTH / 2 + 2"
          :y="RADIUS + STROKE_WIDTH / 2 - 2"
          text-anchor="middle"
          class="pie-center-value"
        >
          {{ totalCount }}
        </text>
        <text
          :x="RADIUS + STROKE_WIDTH / 2 + 2"
          :y="RADIUS + STROKE_WIDTH / 2 + 16"
          text-anchor="middle"
          class="pie-center-label"
        >
          异常总数
        </text>
      </svg>

      <ul class="pie-legend">
        <li v-for="(seg, index) in segments" :key="`${seg.label}-${index}`" class="legend-item">
          <span class="legend-dot" :style="{ backgroundColor: seg.color }" />
          <span class="legend-label">{{ seg.label }}</span>
          <span class="legend-value">{{ seg.value }}</span>
          <span class="legend-percent">
            {{ totalCount ? ((seg.value / totalCount) * 100).toFixed(1) : 0 }}%
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.exception-pie {
  min-height: 200px;
}

.pie-skeleton {
  width: 180px;
  height: 180px;
  margin: 0 auto;
  border-radius: 50%;
}

.pie-body {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.pie-svg {
  width: 180px;
  height: 180px;
  flex: 0 0 auto;
}

.pie-center-value {
  font-size: 26px;
  font-weight: 700;
  fill: var(--text-primary, #303133);
}

.pie-center-label {
  font-size: 12px;
  fill: var(--text-secondary, #909399);
}

.pie-legend {
  flex: 1 1 160px;
  min-width: 140px;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex: 0 0 auto;
}

.legend-label {
  flex: 1 1 auto;
  color: var(--text-regular, #606266);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-value {
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.legend-percent {
  flex: 0 0 48px;
  text-align: right;
  color: var(--text-secondary, #909399);
  font-size: 12px;
}
</style>
