<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { SchedulePackageItem } from '@/types/schedule'
import { goToPackages } from '@/utils/detail-navigation'
import { formatNodeWithName } from '@/utils/schedule-format'

const props = defineProps<{
  packages?: SchedulePackageItem[]
  loading?: boolean
  isDraft?: boolean
}>()

const emit = defineEmits<{
  'open-goods': [code: string]
}>()

const router = useRouter()
const keyword = ref('')

const filteredPackages = computed(() => {
  const list = props.packages ?? []
  const q = keyword.value.trim().toLowerCase()
  if (!q) return list
  return list.filter((row) => {
    const goodsCodes =
      row.goods_items?.map((g) => g.goods_code).join(' ') ?? ''
    return (
      row.package_code.toLowerCase().includes(q) ||
      row.status.toLowerCase().includes(q) ||
      goodsCodes.toLowerCase().includes(q) ||
      (row.from_node_code?.toLowerCase().includes(q) ?? false) ||
      (row.to_node_code?.toLowerCase().includes(q) ?? false) ||
      (row.from_node_name?.toLowerCase().includes(q) ?? false) ||
      (row.to_node_name?.toLowerCase().includes(q) ?? false)
    )
  })
})
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
        <div v-if="packages?.length" class="panel-toolbar">
          <el-input
            v-model="keyword"
            placeholder="搜索包裹/状态/货物/节点"
            clearable
            size="small"
            style="max-width: 280px"
          />
        </div>
        <el-table
          v-if="filteredPackages.length"
          :data="filteredPackages"
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
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="weight" label="重量(kg)" width="90" />
          <el-table-column prop="volume" label="体积(m³)" width="90" />
          <el-table-column label="起点" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatNodeWithName(row.from_node_code, row.from_node_name) }}
            </template>
          </el-table-column>
          <el-table-column label="终点" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatNodeWithName(row.to_node_code, row.to_node_name) }}
            </template>
          </el-table-column>
          <el-table-column label="货物" min-width="160">
            <template #default="{ row }">
              <template v-if="row.goods_items?.length">
                <el-link
                  v-for="(g, idx) in row.goods_items"
                  :key="g.goods_code"
                  type="primary"
                  :underline="false"
                  class="goods-link"
                  @click="emit('open-goods', g.goods_code)"
                >
                  {{ g.goods_code }}<span v-if="idx < row.goods_items!.length - 1">、</span>
                </el-link>
              </template>
              <span v-else>—</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-else-if="packages?.length"
          class="detail-empty"
          description="无匹配的包裹"
          :image-size="64"
        />
        <el-empty
          v-else
          class="detail-empty"
          :description="
            isDraft
              ? '预览方案尚未落库，确认采用后生成包裹'
              : '暂无包裹数据'
          "
          :image-size="64"
        />
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

.panel-toolbar {
  margin-bottom: 12px;
}

.goods-link {
  font-size: inherit;
}
</style>
