<script setup lang="ts">
import { computed, ref } from 'vue'
import type { GoodsScheduleItem } from '@/types/schedule'
import { formatPathWithLabels } from '@/utils/schedule-format'

const props = defineProps<{
  items: GoodsScheduleItem[]
  loading?: boolean
}>()

const emit = defineEmits<{
  'open-goods': [code: string]
  'open-order': [code: string]
}>()

const keyword = ref('')

const filteredItems = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return props.items
  return props.items.filter((row) => {
    const pathText = formatPathWithLabels(row.path, row.path_labels).toLowerCase()
    return (
      row.goods_code.toLowerCase().includes(q) ||
      row.order_code.toLowerCase().includes(q) ||
      (row.goods_name?.toLowerCase().includes(q) ?? false) ||
      row.path.some((p) => p.toLowerCase().includes(q)) ||
      row.path_labels?.some((l) => l.toLowerCase().includes(q)) ||
      pathText.includes(q)
    )
  })
})
</script>

<template>
  <el-collapse class="goods-path-panel enhance-panel">
    <el-collapse-item name="goods-path">
      <template #title>
        <span class="enhance-panel-title">货物路径</span>
        <el-tag v-if="items.length" size="small" type="info" class="panel-count">
          {{ items.length }}
        </el-tag>
      </template>
      <div v-loading="loading">
        <div v-if="items.length" class="panel-toolbar">
          <el-input
            v-model="keyword"
            placeholder="搜索货物/订单/路径/节点名"
            clearable
            size="small"
            style="max-width: 280px"
          />
        </div>
        <el-table
          v-if="filteredItems.length"
          :data="filteredItems"
          stripe
          border
          size="small"
          max-height="360"
        >
          <el-table-column prop="goods_code" label="货物编号" min-width="120">
            <template #default="{ row }">
              <el-link
                type="primary"
                :underline="false"
                @click="emit('open-goods', row.goods_code)"
              >
                {{ row.goods_code }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="order_code" label="订单编号" min-width="120">
            <template #default="{ row }">
              <el-link
                type="primary"
                :underline="false"
                @click="emit('open-order', row.order_code)"
              >
                {{ row.order_code }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column label="路径" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatPathWithLabels(row.path, row.path_labels) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-else-if="items.length"
          class="detail-empty"
          description="无匹配的货物路径"
          :image-size="64"
        />
        <el-empty
          v-else
          class="detail-empty"
          description="请选择调度方案或先生成全局调度"
          :image-size="64"
        />
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.goods-path-panel {
  border: none;
}

.panel-count {
  vertical-align: middle;
}

.panel-toolbar {
  margin-bottom: 12px;
}
</style>
