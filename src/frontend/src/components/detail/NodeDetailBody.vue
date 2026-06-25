<script setup lang="ts">
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import { nodeTypeLabel } from '@/api/nodes'
import type { NodeDetail } from '@/types/node'
import { formatDateTime } from '@/utils/format'

defineProps<{
  data: NodeDetail
}>()
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="节点编号">{{ data.node_code }}</el-descriptions-item>
    <el-descriptions-item label="名称">{{ data.name }}</el-descriptions-item>
    <el-descriptions-item label="类型">
      {{ nodeTypeLabel(data.node_type) }}
    </el-descriptions-item>
    <el-descriptions-item label="地址">{{ data.location }}</el-descriptions-item>
    <el-descriptions-item label="坐标">
      {{ data.latitude }}, {{ data.longitude }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.level != null" label="层级">
      L{{ data.level }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.capacity != null" label="容量">
      {{ data.capacity }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.inventory != null" label="库存">
      {{ data.inventory }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.max_storage_time != null" label="最大存储时间">
      {{ data.max_storage_time }} h
    </el-descriptions-item>
    <el-descriptions-item v-if="data.created_at" label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.updated_at" label="更新时间">
      {{ formatDateTime(data.updated_at) }}
    </el-descriptions-item>
  </DetailDescriptions>
</template>
