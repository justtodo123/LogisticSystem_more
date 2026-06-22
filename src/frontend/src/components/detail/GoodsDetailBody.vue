<script setup lang="ts">
import { useRouter } from 'vue-router'
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import { GOODS_STATUS_MAP } from '@/constants/status'
import type { GoodsDetail, GoodsStatus } from '@/types/goods'
import { formatDateTime } from '@/utils/format'
import { goToOrders } from '@/utils/detail-navigation'

defineProps<{
  data: GoodsDetail
}>()

const router = useRouter()

function statusLabel(status: GoodsStatus): string {
  return GOODS_STATUS_MAP[status]?.label ?? status
}
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="货物编号">{{ data.goods_code }}</el-descriptions-item>
    <el-descriptions-item label="名称">{{ data.goods_name }}</el-descriptions-item>
    <el-descriptions-item label="类型">{{ data.goods_type }}</el-descriptions-item>
    <el-descriptions-item label="重量 / 体积">
      {{ data.weight }} kg / {{ data.volume }} m³
    </el-descriptions-item>
    <el-descriptions-item label="所在节点">
      {{ data.node_name || data.node_code }}
      <span class="detail-sub">（{{ data.node_code }}）</span>
    </el-descriptions-item>
    <el-descriptions-item label="所属订单">
      <el-link
        type="primary"
        :underline="false"
        @click="goToOrders(router, data.order_code)"
      >
        {{ data.order_code }}
      </el-link>
    </el-descriptions-item>
    <el-descriptions-item label="状态">{{ statusLabel(data.status) }}</el-descriptions-item>
    <el-descriptions-item v-if="data.created_at" label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.updated_at" label="更新时间">
      {{ formatDateTime(data.updated_at) }}
    </el-descriptions-item>
  </DetailDescriptions>
</template>
