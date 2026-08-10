<script setup lang="ts">
import { computed, ref } from 'vue'
import { FullScreen, RefreshRight, ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import type { RouteCoordinates, RoutePackagePoint } from '@/types/route'
import {
  collectGeoPoints,
  computeBounds,
  projectPoint,
} from '@/utils/geo-projection'
import { isAmapConfigured } from '@/utils/load-amap'
import AmapRouteMap from './AmapRouteMap.vue'
import RouteMapViewport from './RouteMapViewport.vue'

const props = withDefaults(
  defineProps<{
    data: RouteCoordinates | null
    loading?: boolean
    strokeColor?: string
    emptyDescription?: string
  }>(),
  {
    strokeColor: '#409eff',
    emptyDescription: '请选择车辆查看路线',
  },
)

const emit = defineEmits<{
  'package-click': [pkg: RoutePackagePoint]
}>()

const INLINE_WIDTH = 640
const INLINE_HEIGHT = 360
const FULLSCREEN_WIDTH = 960
const FULLSCREEN_HEIGHT = 560

const fullscreenVisible = ref(false)
const inlineViewportRef = ref<InstanceType<typeof RouteMapViewport> | null>(null)
const fullscreenViewportRef = ref<InstanceType<typeof RouteMapViewport> | null>(null)
const inlineAmapRef = ref<InstanceType<typeof AmapRouteMap> | null>(null)
const fullscreenAmapRef = ref<InstanceType<typeof AmapRouteMap> | null>(null)

// T5-2：配置了 VITE_MAP_API_KEY 时优先使用真实高德地图；加载失败降级为 Canvas/SVG
const useAmap = ref(isAmapConfigured())

function onAmapLoadError(): void {
  useAmap.value = false
}

function projectRoute(width: number, height: number) {
  const data = props.data
  if (!data) return null

  const bounds = computeBounds(
    collectGeoPoints({
      nodes: data.nodes,
      packages: data.packages,
      segments: data.segments,
    }),
  )
  if (!bounds) return null

  const size = { width, height, padding: 36 }

  const matchNode = (lat: number, lng: number) =>
    data.nodes.find(
      (n) =>
        Math.abs(n.latitude - lat) < 1e-5 && Math.abs(n.longitude - lng) < 1e-5,
    )

  return {
    bounds,
    segments: data.segments.map((seg) => {
      const start = projectPoint(seg.start_lat, seg.start_lng, bounds, size)
      const end = projectPoint(seg.end_lat, seg.end_lng, bounds, size)
      const fromNode = matchNode(seg.start_lat, seg.start_lng)
      const toNode = matchNode(seg.end_lat, seg.end_lng)
      const directionLabel =
        fromNode && toNode
          ? `${fromNode.node_code} → ${toNode.node_code}`
          : undefined
      return {
        ...seg,
        x1: start.x,
        y1: start.y,
        x2: end.x,
        y2: end.y,
        directionLabel,
      }
    }),
    nodes: data.nodes.map((node) => {
      const p = projectPoint(node.latitude, node.longitude, bounds, size)
      return { ...node, x: p.x, y: p.y }
    }),
    packages: data.packages.map((pkg) => {
      const p = projectPoint(pkg.latitude, pkg.longitude, bounds, size)
      return { ...pkg, x: p.x, y: p.y }
    }),
  }
}

const inlineProjected = computed(() =>
  projectRoute(INLINE_WIDTH, INLINE_HEIGHT),
)

const fullscreenProjected = computed(() =>
  projectRoute(FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT),
)

function zoomInline(factor: number): void {
  if (useAmap.value) {
    inlineAmapRef.value?.zoomBy(factor)
  } else {
    inlineViewportRef.value?.zoomBy(factor)
  }
}

function resetInline(): void {
  if (useAmap.value) {
    inlineAmapRef.value?.resetView()
  } else {
    inlineViewportRef.value?.resetView()
  }
}

function openFullscreen(): void {
  fullscreenVisible.value = true
}

function onFullscreenOpened(): void {
  if (useAmap.value) {
    fullscreenAmapRef.value?.resetView()
  } else {
    fullscreenViewportRef.value?.resetView()
  }
}
</script>

<template>
  <div v-loading="loading" class="route-map-wrap">
    <!-- T5-2：高德地图模式 -->
    <template v-if="useAmap">
      <div class="route-map-toolbar">
        <el-button-group size="small">
          <el-button :icon="ZoomIn" title="放大" @click="zoomInline(1.2)" />
          <el-button :icon="ZoomOut" title="缩小" @click="zoomInline(0.84)" />
          <el-button :icon="RefreshRight" title="重置视图" @click="resetInline" />
        </el-button-group>
        <el-button
          size="small"
          type="primary"
          plain
          :icon="FullScreen"
          @click="openFullscreen"
        >
          全屏查看
        </el-button>
      </div>

      <AmapRouteMap
        v-if="data"
        ref="inlineAmapRef"
        :data="data"
        :stroke-color="strokeColor"
        :height="INLINE_HEIGHT"
        @package-click="emit('package-click', $event)"
        @load-error="onAmapLoadError"
      />
      <el-empty v-else :description="emptyDescription" />

      <div v-if="data" class="route-map-meta">
        <span>路线 {{ data.route_code }}</span>
        <span>带货距离 {{ data.total_distance.toFixed(1) }} km</span>
        <span>带货时间 {{ data.total_time.toFixed(0) }} min</span>
        <span class="route-map-legend">
          <i class="legend-dot legend-node" />节点
          <i class="legend-dot legend-pkg" />包裹
          <i class="legend-arrow" />真实道路路径
        </span>
      </div>
    </template>

    <!-- 降级模式：Canvas/SVG 示意画线 -->
    <template v-else>
      <el-empty
        v-if="!loading && !inlineProjected"
        :description="emptyDescription"
      />

      <template v-else-if="inlineProjected">
        <div class="route-map-toolbar">
          <el-button-group size="small">
            <el-button :icon="ZoomIn" title="放大" @click="zoomInline(1.2)" />
            <el-button :icon="ZoomOut" title="缩小" @click="zoomInline(0.84)" />
            <el-button :icon="RefreshRight" title="重置视图" @click="resetInline" />
          </el-button-group>
          <el-button
            size="small"
            type="primary"
            plain
            :icon="FullScreen"
            @click="openFullscreen"
          >
            全屏查看
          </el-button>
        </div>

        <RouteMapViewport
          ref="inlineViewportRef"
          :projected="inlineProjected"
          :stroke-color="strokeColor"
          :width="INLINE_WIDTH"
          :height="INLINE_HEIGHT"
          @package-click="emit('package-click', $event)"
        />

        <div v-if="data" class="route-map-meta">
          <span>路线 {{ data.route_code }}</span>
          <span>带货距离 {{ data.total_distance.toFixed(1) }} km</span>
          <span>带货时间 {{ data.total_time.toFixed(0) }} min</span>
          <span class="route-map-legend">
            <i class="legend-dot legend-node" />节点
            <i class="legend-dot legend-pkg" />包裹
            <i class="legend-arrow" />带货路段方向
          </span>
        </div>
      </template>
    </template>

    <el-dialog
      v-model="fullscreenVisible"
      title="路线全屏查看"
      width="92%"
      top="4vh"
      destroy-on-close
      class="route-map-dialog"
      @opened="onFullscreenOpened"
    >
      <AmapRouteMap
        v-if="useAmap && data"
        ref="fullscreenAmapRef"
        :data="data"
        :stroke-color="strokeColor"
        :height="FULLSCREEN_HEIGHT"
        @package-click="emit('package-click', $event)"
        @load-error="onAmapLoadError"
      />
      <RouteMapViewport
        v-else-if="fullscreenProjected"
        ref="fullscreenViewportRef"
        :projected="fullscreenProjected"
        :stroke-color="strokeColor"
        :width="FULLSCREEN_WIDTH"
        :height="FULLSCREEN_HEIGHT"
        @package-click="emit('package-click', $event)"
      />
      <div v-if="data" class="route-map-meta route-map-meta--dialog">
        <span>路线 {{ data.route_code }}</span>
        <span>带货距离 {{ data.total_distance.toFixed(1) }} km</span>
        <span>带货时间 {{ data.total_time.toFixed(0) }} min</span>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.route-map-wrap {
  min-height: 200px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: #fafafa;
  padding: 8px;
}

.route-map-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.route-map-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
}

.route-map-meta--dialog {
  margin-top: 12px;
}

.route-map-legend {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #909399;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 2px;
  vertical-align: middle;
}

.legend-node {
  background: #f56c6c;
}

.legend-pkg {
  background: #409eff;
}

.legend-arrow {
  display: inline-block;
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 7px solid #409eff;
  margin-right: 2px;
  vertical-align: middle;
}
</style>
