<script setup lang="ts">
import type { RouteVehicleOption } from '@/utils/route-vehicles'

defineProps<{
  vehicles: RouteVehicleOption[]
  selectedVehicleCode: string
  loading?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:selectedVehicleCode': [value: string]
}>()
</script>

<template>
  <div class="vehicle-picker">
    <el-empty
      v-if="!loading && !vehicles.length"
      description="请先生成节点间调度，再选择车辆查看路线"
    />
    <el-radio-group
      v-else
      :model-value="selectedVehicleCode"
      :disabled="disabled || loading"
      class="vehicle-radio-group"
      @update:model-value="emit('update:selectedVehicleCode', $event as string)"
    >
      <el-radio-button
        v-for="item in vehicles"
        :key="item.vehicle_code"
        :value="item.vehicle_code"
      >
        {{ item.vehicle_code }}
      </el-radio-button>
    </el-radio-group>
  </div>
</template>

<style scoped>
.vehicle-picker {
  margin-bottom: 12px;
}

.vehicle-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
