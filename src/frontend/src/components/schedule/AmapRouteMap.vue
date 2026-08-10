<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { loadAmap, isAmapConfigured } from '@/utils/load-amap'
import { computeBounds, collectGeoPoints } from '@/utils/geo-projection'
import type { RouteCoordinates, RoutePackagePoint } from '@/types/route'

const props = withDefaults(
  defineProps<{
    data: RouteCoordinates | null
    strokeColor?: string
    height?: number
  }>(),
  {
    strokeColor: '#409eff',
    height: 360,
  },
)

const emit = defineEmits<{
  'package-click': [pkg: RoutePackagePoint]
  'load-error': []
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const loadFailed = ref(false)

const apiKey = import.meta.env.VITE_MAP_API_KEY || ''

let map: any = null
let AMap: any = null
let driving: any = null
let markerObjs: any[] = []
let layerObjs: any[] = []
let disposed = false

function clearLayers(): void {
  markerObjs.forEach((m) => map?.remove(m))
  markerObjs = []
  layerObjs.forEach((l) => map?.remove(l))
  layerObjs = []
  if (driving) {
    try {
      driving.clear()
    } catch {
      /* ignore */
    }
    driving = null
  }
}

function addMarkers(data: RouteCoordinates): void {
  if (!map || !AMap) return
  for (const node of data.nodes) {
    const marker = new AMap.Marker({
      position: [node.longitude, node.latitude],
      content: `<div class="amap-node-marker" title="${node.node_code}">${node.node_code.slice(0, 2)}</div>`,
      offset: new AMap.Pixel(-12, -12),
      zIndex: 120,
    })
    markerObjs.push(marker)
    map.add(marker)
  }
  for (const pkg of data.packages) {
    const marker = new AMap.Marker({
      position: [pkg.longitude, pkg.latitude],
      content: '<div class="amap-pkg-marker"></div>',
      offset: new AMap.Pixel(-5, -5),
      title: pkg.package_code,
      zIndex: 110,
    })
    marker.on('click', () => emit('package-click', pkg))
    markerObjs.push(marker)
    map.add(marker)
  }
}

function addPolylines(data: RouteCoordinates): void {
  if (!map || !AMap) return
  for (const seg of data.segments) {
    const polyline = new AMap.Polyline({
      path: [
        [seg.start_lng, seg.start_lat],
        [seg.end_lng, seg.end_lat],
      ],
      strokeColor: props.strokeColor,
      strokeWeight: 4,
      strokeOpacity: 0.85,
      strokeStyle: 'solid',
      zIndex: 100,
    })
    layerObjs.push(polyline)
    map.add(polyline)
  }
}

/** 用 AMap.Driving 在真实路网上绘制每一段路径（失败由调用方降级为折线） */
async function drawRoadPaths(data: RouteCoordinates): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    AMap.plugin(['AMap.Driving'], (err: any) => (err ? reject(err) : resolve()))
  })
  driving = new AMap.Driving({
    map,
    hideMarkers: true,
    showTraffic: false,
    autoFitView: false,
  })
  for (const seg of data.segments) {
    await new Promise<void>((resolve) => {
      driving.search(
        new AMap.LngLat(seg.start_lng, seg.start_lat),
        new AMap.LngLat(seg.end_lng, seg.end_lat),
        () => resolve(),
      )
    })
  }
}

async function renderRoute(): Promise<void> {
  if (!map || !AMap || !props.data) return
  clearLayers()
  addMarkers(props.data)
  try {
    await drawRoadPaths(props.data)
  } catch {
    // 驾车规划不可用 → 直线折线
    addPolylines(props.data)
  }
  fitToRoute(props.data)
}

function fitToRoute(data: RouteCoordinates): void {
  if (!map || !AMap) return
  const points = collectGeoPoints({
    nodes: data.nodes,
    packages: data.packages,
    segments: data.segments,
  })
  if (!points.length) return
  const bounds = computeBounds(points)
  if (!bounds) return
  map.setBounds(
    new AMap.Bounds(
      new AMap.LngLat(bounds.minLng, bounds.minLat),
      new AMap.LngLat(bounds.maxLng, bounds.maxLat),
    ),
  )
}

function zoomBy(factor: number): void {
  if (map) map.setZoom(Math.min(19, Math.max(3, map.getZoom() * factor)))
}

function resetView(): void {
  if (map && props.data) fitToRoute(props.data)
}

defineExpose({ zoomBy, resetView })

onMounted(async () => {
  if (!isAmapConfigured() || !apiKey) {
    loadFailed.value = true
    loading.value = false
    emit('load-error')
    return
  }
  try {
    AMap = await loadAmap(apiKey)
    if (disposed || !containerRef.value) return
    map = new AMap.Map(containerRef.value, {
      zoom: 10,
      center: [114.3, 30.58],
      viewMode: '2D',
    })
    if (props.data) await renderRoute()
  } catch {
    if (!disposed) {
      loadFailed.value = true
      emit('load-error')
    }
  } finally {
    loading.value = false
  }
})

watch(
  () => props.data,
  () => {
    if (map && AMap && props.data && !disposed) void renderRoute()
  },
)

onBeforeUnmount(() => {
  disposed = true
  clearLayers()
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<template>
  <div
    v-loading="loading"
    class="amap-route-map"
    :style="{ height: `${height}px` }"
  >
    <div v-if="loadFailed" class="amap-route-map--fallback">
      高德地图加载失败，已降级为示意画线
    </div>
    <div ref="containerRef" class="amap-route-map--canvas" />
  </div>
</template>

<style scoped>
.amap-route-map {
  position: relative;
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f7fa;
}

.amap-route-map--canvas {
  width: 100%;
  height: 100%;
}

.amap-route-map--fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #909399;
}
</style>

<style>
/* 高德 Marker content 注入到地图容器（非 scoped），需要全局样式 */
.amap-node-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f56c6c;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.amap-pkg-marker {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409eff;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  cursor: pointer;
}
</style>
