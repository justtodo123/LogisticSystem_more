<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { RoutePackagePoint } from '@/types/route'

export interface ProjectedRoute {
  segments: Array<{
    road_name: string
    x1: number
    y1: number
    x2: number
    y2: number
    directionLabel?: string
  }>
  nodes: Array<{
    node_code: string
    x: number
    y: number
  }>
  packages: Array<RoutePackagePoint & { x: number; y: number }>
}

const props = withDefaults(
  defineProps<{
    projected: ProjectedRoute
    strokeColor?: string
    width?: number
    height?: number
    interactive?: boolean
  }>(),
  {
    strokeColor: '#409eff',
    width: 640,
    height: 360,
    interactive: true,
  },
)

const emit = defineEmits<{
  'package-click': [pkg: RoutePackagePoint]
}>()

const uid = `route-arrow-${Math.random().toString(36).slice(2, 9)}`
const markerId = `${uid}-end`

const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const dragging = ref(false)
const lastPointer = { x: 0, y: 0 }

const viewTransform = computed(
  () => `translate(${panX.value} ${panY.value}) scale(${scale.value})`,
)

function clampScale(value: number): number {
  return Math.min(5, Math.max(0.4, value))
}

function zoomBy(factor: number): void {
  scale.value = clampScale(scale.value * factor)
}

function resetView(): void {
  scale.value = 1
  panX.value = 0
  panY.value = 0
}

function onWheel(event: WheelEvent): void {
  if (!props.interactive) return
  event.preventDefault()
  const factor = event.deltaY > 0 ? 0.9 : 1.1
  zoomBy(factor)
}

function onPointerDown(event: PointerEvent): void {
  if (!props.interactive) return
  dragging.value = true
  lastPointer.x = event.clientX
  lastPointer.y = event.clientY
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent): void {
  if (!dragging.value) return
  panX.value += event.clientX - lastPointer.x
  panY.value += event.clientY - lastPointer.y
  lastPointer.x = event.clientX
  lastPointer.y = event.clientY
}

function onPointerUp(event: PointerEvent): void {
  dragging.value = false
  try {
    ;(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId)
  } catch {
    /* ignore */
  }
}

defineExpose({ resetView, zoomBy })

onMounted(() => {
  resetView()
})

onBeforeUnmount(() => {
  dragging.value = false
})
</script>

<template>
  <div
    class="route-map-viewport"
    :class="{ 'is-dragging': dragging, interactive }"
    @wheel="onWheel"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @pointerleave="onPointerUp"
  >
    <svg
      class="route-map-svg"
      :viewBox="`0 0 ${width} ${height}`"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <marker
          :id="markerId"
          markerWidth="8"
          markerHeight="8"
          refX="7"
          refY="4"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0 L8,4 L0,8 Z" :fill="strokeColor" />
        </marker>
      </defs>

      <g :transform="viewTransform">
        <line
          v-for="(seg, idx) in projected.segments"
          :key="`seg-${idx}`"
          :x1="seg.x1"
          :y1="seg.y1"
          :x2="seg.x2"
          :y2="seg.y2"
          :stroke="strokeColor"
          stroke-width="2"
          stroke-linecap="round"
          :marker-end="`url(#${markerId})`"
        >
          <title>{{ seg.road_name }}（{{ seg.directionLabel ?? '起点 → 终点' }}）</title>
        </line>

        <g v-for="node in projected.nodes" :key="node.node_code">
          <circle
            :cx="node.x"
            :cy="node.y"
            r="6"
            fill="#f56c6c"
            stroke="#fff"
            stroke-width="1.5"
          />
          <text
            :x="node.x + 8"
            :y="node.y + 4"
            class="route-label"
            fill="#303133"
          >
            {{ node.node_code }}
          </text>
        </g>

        <g
          v-for="pkg in projected.packages"
          :key="pkg.package_code"
          class="pkg-hit"
          @click.stop="emit('package-click', pkg)"
        >
          <circle
            :cx="pkg.x"
            :cy="pkg.y"
            r="5"
            fill="#409eff"
            stroke="#fff"
            stroke-width="1.5"
          />
          <title>{{ pkg.package_code }}</title>
        </g>
      </g>
    </svg>

    <p v-if="interactive" class="route-map-hint">
      滚轮缩放 · 拖拽平移
    </p>
  </div>
</template>

<style scoped>
.route-map-viewport {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  background: #fff;
}

.route-map-viewport.interactive {
  cursor: grab;
}

.route-map-viewport.is-dragging {
  cursor: grabbing;
}

.route-map-svg {
  width: 100%;
  height: auto;
  display: block;
  touch-action: none;
}

.route-label {
  font-size: 11px;
  user-select: none;
  pointer-events: none;
}

.pkg-hit {
  cursor: pointer;
}

.route-map-hint {
  position: absolute;
  right: 8px;
  bottom: 6px;
  margin: 0;
  padding: 2px 8px;
  font-size: 11px;
  color: #909399;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 3px;
  pointer-events: none;
  user-select: none;
}
</style>
