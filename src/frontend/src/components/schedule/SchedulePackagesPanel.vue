<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { SchedulePackageItem } from '@/types/schedule'
import { goToPackages } from '@/utils/detail-navigation'

defineProps<{
  packages?: SchedulePackageItem[]
  loading?: boolean
}>()

const router = useRouter()

function formatGoods(items?: { goods_code: string }[]): string {
  if (!items?.length) return '—'
  return items.map((g) => g.goods_code).join('、')
}
</script>

<template>
  <el-collapse class="schedule-packages-panel enhance-panel">
    <el-collapse-item name="packages">
      <template #title>
        <span class="enhance-panel-title">方案包裹一览</span>
        <el-tag v-if="packages?.length" size="small" type="info" class="panel-count">
          {{ packages.length }}
        </el-tag>
      </template>
      <div v-loading="loading">
        <el-table
          v-if="packages?.length"
          :data="packages"
          size="small"
          stripe
          border
          max-height="320"
        >
          <el-table-column prop="package_code" label="包裹编号" min-width="130">
            <template #default="{ row }">
              <el-link
                type="primary"
                :underline="false"
                @click="goToPackages(router, { package_code: row.package_code })"
              >
                {{ row.package_code }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column prop="weight" label="重量(kg)" width="90" />
          <el-table-column prop="volume" label="体积(m³)" width="90" />
          <el-table-column prop="from_node_code" label="起点" width="90" />
          <el-table-column prop="to_node_code" label="终点" width="90" />
          <el-table-column label="货物" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatGoods(row.goods_items) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else class="detail-empty" description="暂无包裹数据" :image-size="64" />
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.schedule-packages-panel {
  border: none;
}

.panel-count {
  vertical-align: middle;
}
</style>
