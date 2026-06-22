<script setup lang="ts">
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import { ORDER_STATUS_MAP } from '@/constants/status'
import type { OrderDetail, OrderStatus } from '@/types/order'
import { formatDateTime } from '@/utils/format'

defineProps<{
  data: OrderDetail
}>()

function statusLabel(status: OrderStatus): string {
  return ORDER_STATUS_MAP[status]?.label ?? status
}
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="订单编号">{{ data.order_code }}</el-descriptions-item>
    <el-descriptions-item label="目的地">
      {{ data.destination_node_name || data.destination_node_code }}
      <span class="detail-sub">（{{ data.destination_node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item label="时效要求">{{ data.time_window }}</el-descriptions-item>
    <el-descriptions-item label="状态">{{ statusLabel(data.status) }}</el-descriptions-item>
    <el-descriptions-item label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.updated_at" label="更新时间">
      {{ formatDateTime(data.updated_at) }}
    </el-descriptions-item>
  </DetailDescriptions>

  <p class="detail-section-title">货物明细（{{ data.goods?.length ?? 0 }}）</p>
  <el-table
    v-if="data.goods?.length"
    :data="data.goods"
    size="small"
    border
    stripe
    max-height="280"
  >
    <el-table-column prop="goods_code" label="货物编号" min-width="120" />
    <el-table-column prop="goods_name" label="名称" min-width="100" />
    <el-table-column prop="goods_type" label="类型" width="90" />
    <el-table-column prop="weight" label="重量" width="80" />
    <el-table-column prop="volume" label="体积" width="80" />
    <el-table-column prop="status" label="状态" width="90" />
  </el-table>
  <el-empty v-else class="detail-empty" description="暂无货物" :image-size="64" />
</template>
