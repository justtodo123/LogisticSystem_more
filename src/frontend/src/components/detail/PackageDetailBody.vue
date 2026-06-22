<script setup lang="ts">
import { useRouter } from 'vue-router'
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import { PACKAGE_STATUS_MAP } from '@/constants/status'
import type { PackageDetail, PackageStatus } from '@/types/package'
import { formatDateTime } from '@/utils/format'
import { goToOrders } from '@/utils/detail-navigation'

defineProps<{
  data: PackageDetail
}>()

const router = useRouter()

function statusLabel(status: PackageStatus): string {
  return PACKAGE_STATUS_MAP[status]?.label ?? status
}
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="包裹编号">{{ data.package_code }}</el-descriptions-item>
    <el-descriptions-item label="状态">{{ statusLabel(data.status) }}</el-descriptions-item>
    <el-descriptions-item label="重量 / 体积">
      {{ data.weight }} kg / {{ data.volume }} m³
    </el-descriptions-item>
    <el-descriptions-item label="起点">
      {{ data.from_node_name || data.from_node_code }}
      <span class="detail-sub">（{{ data.from_node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item label="终点">
      {{ data.to_node_name || data.to_node_code }}
      <span class="detail-sub">（{{ data.to_node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item v-if="data.dispatch_code" label="调度批次">
      {{ data.dispatch_code }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.created_at" label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.updated_at" label="更新时间">
      {{ formatDateTime(data.updated_at) }}
    </el-descriptions-item>
  </DetailDescriptions>

  <p class="detail-section-title">货物明细</p>
  <el-table
    v-if="data.goods_items?.length"
    :data="data.goods_items"
    size="small"
    border
    stripe
  >
    <el-table-column prop="goods_code" label="货物编号" min-width="120" />
    <el-table-column label="所属订单" min-width="120">
      <template #default="{ row }">
        <el-link
          v-if="row.order_code"
          type="primary"
          :underline="false"
          @click="goToOrders(router, row.order_code)"
        >
          {{ row.order_code }}
        </el-link>
        <span v-else>—</span>
      </template>
    </el-table-column>
  </el-table>
  <el-empty v-else class="detail-empty" description="暂无货物明细" :image-size="64" />
</template>
