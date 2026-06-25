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
    <template v-else>
      <el-select
        :model-value="selectedVehicleCode"
        filterable
        clearable
        placeholder="输入或选择车辆编号"
        :disabled="disabled || loading"
        class="vehicle-select"
        @update:model-value="emit('update:selectedVehicleCode', $event ?? '')"
      >
        <el-option
          v-for="item in vehicles"
          :key="item.vehicle_code"
          :label="item.vehicle_code"
          :value="item.vehicle_code"
        />
      </el-select>
      <span v-if="vehicles.length" class="vehicle-count">共 {{ vehicles.length }} 辆车</span>
    </template>
  </div>
</template>

<style scoped>
.vehicle-picker {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.vehicle-select {
  width: 240px;
}

.vehicle-count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
