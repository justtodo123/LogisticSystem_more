<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CostNodeItem, CostVehicleItem } from '@/types/report'

const props = defineProps<{
  nodes: CostNodeItem[]
  vehicles: CostVehicleItem[]
  loading?: boolean
}>()

type ViewKey = 'node' | 'vehicle'

const view = ref<ViewKey>('node')

interface BarItem {
  label: string
  cost: number
  sub: string
}

const items = computed<BarItem[]>(() => {
  if (view.value === 'node') {
    return props.nodes.map((n) => ({
      label: n.node_code,
      cost: n.cost,
      sub: `${n.route_count} 条路线`,
    }))
  }
  return props.vehicles.map((v) => ({
    label: v.vehicle_code,
    cost: v.cost,
    sub: `${v.distance_km.toFixed(1)} km · ${v.route_count} 条路线`,
  }))
})

const maxCost = computed(() => {
  const max = Math.max(0, ...items.value.map((i) => i.cost))
  return max > 0 ? max : 1
})

const empty = computed(() => !items.value.length && !props.loading)
</script>

<template>
  <div class="cost-trend">
    <div class="chart-toolbar">
      <el-radio-group v-model="view" size="small" :disabled="loading">
        <el-radio-button value="node">按节点</el-radio-button>
        <el-radio-button value="vehicle">按车辆</el-radio-button>
      </el-radio-group>
    </div>

    <el-skeleton v-if="loading" :rows="5" animated />

    <el-empty v-else-if="empty" description="暂无成本数据" :image-size="72" />

    <div v-else class="bar-list">
      <div v-for="item in items" :key="item.label" class="bar-row">
        <div class="bar-label" :title="item.label">{{ item.label }}</div>
        <div class="bar-track">
          <div
            class="bar-fill"
            :style="{
              width: `${(item.cost / maxCost) * 100}%`,
              backgroundColor: '#409eff',
            }"
          />
        </div>
        <div class="bar-value">{{ item.cost.toFixed(0) }} 元</div>
        <div class="bar-sub">{{ item.sub }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cost-trend {
  min-height: 200px;
}

.chart-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.bar-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar-label {
  flex: 0 0 84px;
  font-size: 13px;
  color: var(--text-regular, #606266);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  flex: 1 1 auto;
  height: 14px;
  border-radius: 7px;
  background-color: var(--meta-bg, #f5f7fa);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 7px;
  transition: width 0.4s ease;
}

.bar-value {
  flex: 0 0 68px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #303133);
  text-align: right;
}

.bar-sub {
  flex: 0 0 96px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
  text-align: right;
}
</style>
