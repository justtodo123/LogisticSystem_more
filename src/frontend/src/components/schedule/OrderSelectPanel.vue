<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { listLevel0SortingCenters } from '@/api/nodes'
import { listOrders } from '@/api/orders'
import { ORDER_STATUS_OPTIONS } from '@/constants/status'
import type { NodeItem } from '@/types/node'
import type { Order, OrderStatus } from '@/types/order'

const emit = defineEmits<{
  'selection-change': [codes: string[]]
}>()

const loading = ref(false)
const items = ref<Order[]>([])
const selectedRows = ref<Order[]>([])
const destinationOptions = ref<NodeItem[]>([])

const filters = reactive<{
  status: OrderStatus | ''
  destination_node_code: string
}>({
  status: 'pending',
  destination_node_code: '',
})

async function loadOrders(): Promise<void> {
  loading.value = true
  try {
    const result = await listOrders({
      page: 1,
      page_size: 200,
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.destination_node_code
        ? { destination_node_code: filters.destination_node_code }
        : {}),
    })
    items.value = result.items
    const codes = new Set(selectedRows.value.map((r) => r.order_code))
    selectedRows.value = result.items.filter((o) => codes.has(o.order_code))
    emitSelection()
  } finally {
    loading.value = false
  }
}

function emitSelection(): void {
  emit(
    'selection-change',
    selectedRows.value.map((r) => r.order_code),
  )
}

function onSelectionChange(rows: Order[]): void {
  selectedRows.value = rows
  emitSelection()
}

onMounted(async () => {
  destinationOptions.value = await listLevel0SortingCenters()
  await loadOrders()
})

watch(filters, () => {
  void loadOrders()
})
</script>

<template>
  <el-collapse class="order-select-panel enhance-panel">
    <el-collapse-item name="orders">
      <template #title>
        <span class="enhance-panel-title">订单选择（预览调度）</span>
        <el-tag v-if="selectedRows.length" size="small" type="info" class="panel-count">
          已选 {{ selectedRows.length }}
        </el-tag>
        <el-tag v-else size="small" type="warning" class="panel-count">
          未选则预览全部 pending
        </el-tag>
      </template>

      <div v-loading="loading">
        <div class="panel-filters">
          <el-select
            v-model="filters.status"
            placeholder="订单状态"
            clearable
            size="small"
            style="width: 140px"
          >
            <el-option
              v-for="opt in ORDER_STATUS_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <el-select
            v-model="filters.destination_node_code"
            placeholder="目的地节点"
            clearable
            filterable
            size="small"
            style="width: 220px"
          >
            <el-option
              v-for="node in destinationOptions"
              :key="node.node_code"
              :label="`${node.name} (${node.node_code})`"
              :value="node.node_code"
            />
          </el-select>
        </div>

        <el-table
          :data="items"
          size="small"
          stripe
          border
          max-height="280"
          @selection-change="onSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column prop="order_code" label="订单编号" min-width="130" />
          <el-table-column prop="destination_node_name" label="目的地" min-width="140" />
          <el-table-column prop="time_window" label="时间窗" width="120" />
          <el-table-column prop="status" label="状态" width="100" />
        </el-table>
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.order-select-panel {
  margin-bottom: 16px;
  border: none;
}

.panel-count {
  margin-left: 8px;
  vertical-align: middle;
}

.panel-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}
</style>
