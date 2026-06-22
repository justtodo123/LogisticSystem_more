<script setup lang="ts">
import { useRouter } from 'vue-router'
import DetailDescriptions from '@/components/detail/DetailDescriptions.vue'
import type { ExceptionEvent } from '@/types/exception'
import { formatDateTime } from '@/utils/format'
import { goToDashboardSchedule } from '@/utils/detail-navigation'

defineProps<{
  data: ExceptionEvent
}>()

const router = useRouter()

const TYPE_LABEL: Record<string, string> = {
  node: '节点异常',
  road: '道路异常',
}

const ACTION_LABEL: Record<string, string> = {
  redispatch: '重新调度',
  reroute: '重新规划路径',
}
</script>

<template>
  <DetailDescriptions>
    <el-descriptions-item label="事件编号">{{ data.event_code }}</el-descriptions-item>
    <el-descriptions-item label="类型">
      {{ TYPE_LABEL[data.exception_type] ?? data.exception_type }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.exception_subtype" label="子类型">
      {{ data.exception_subtype }}
    </el-descriptions-item>
    <el-descriptions-item label="推荐动作">
      {{ ACTION_LABEL[data.recommended_action] ?? data.recommended_action }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.target_type" label="目标类型">
      {{ data.target_type }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.target_code" label="目标编号">
      {{ data.target_code }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.related_schedule_code" label="关联方案">
      <el-link
        type="primary"
        :underline="false"
        @click="goToDashboardSchedule(router, data.related_schedule_code!)"
      >
        {{ data.related_schedule_code }}
      </el-link>
    </el-descriptions-item>
    <el-descriptions-item v-if="data.replan_batch_code" label="重规划批次">
      {{ data.replan_batch_code }}
    </el-descriptions-item>
    <el-descriptions-item label="状态">
      {{ data.status === 'open' ? '待处理' : '已解决' }}
    </el-descriptions-item>
    <el-descriptions-item label="描述">{{ data.description }}</el-descriptions-item>
    <el-descriptions-item v-if="data.created_at" label="创建时间">
      {{ formatDateTime(data.created_at) }}
    </el-descriptions-item>
    <el-descriptions-item v-if="data.resolved_at" label="解决时间">
      {{ formatDateTime(data.resolved_at) }}
    </el-descriptions-item>
  </DetailDescriptions>
</template>
