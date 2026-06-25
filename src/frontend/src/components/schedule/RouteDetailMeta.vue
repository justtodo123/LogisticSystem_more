<script setup lang="ts">
import { ref, watch } from 'vue'
import { getRouteDetail } from '@/api/routes'
import type { RouteCoordinates } from '@/types/route'

const props = defineProps<{
  coordinates: RouteCoordinates | null
}>()

const emission = ref<number | null>(null)
const loading = ref(false)

watch(
  () => props.coordinates?.route_code,
  async (routeCode) => {
    emission.value = null
    if (!routeCode) return
    loading.value = true
    try {
      const detail = await getRouteDetail(routeCode)
      emission.value = detail.total_emission ?? null
    } catch {
      emission.value = null
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)
</script>

<template>
  <div
    v-if="coordinates"
    v-loading="loading"
    element-loading-text="加载路线指标…"
    class="route-detail-meta enhance-meta-bar"
  >
    <span>路线 {{ coordinates.route_code }}</span>
    <span>距离 {{ coordinates.total_distance?.toFixed(1) ?? '—' }} km</span>
    <span>时间 {{ coordinates.total_time?.toFixed(0) ?? '—' }} min</span>
    <span v-if="emission != null">碳排放 {{ emission.toFixed(2) }} kg CO₂e</span>
  </div>
</template>
