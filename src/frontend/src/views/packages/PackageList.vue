<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import { listNodes } from '@/api/nodes'
import { listPackages } from '@/api/packages'
import { PACKAGE_STATUS_MAP, PACKAGE_STATUS_OPTIONS } from '@/constants/status'
import type { NodeItem } from '@/types/node'
import type { PackageGoodsItem, PackageItem, PackageStatus } from '@/types/package'
import { formatDateTime } from '@/utils/format'

const {
  items,
  total,
  page,
  pageSize,
  loading,
  filters,
  onPageChange,
  onSizeChange,
  applyFilters,
} = usePagedList<PackageItem>((params) => listPackages(params), {
  status: '',
  from_node_code: '',
  to_node_code: '',
})

const nodeOptions = ref<NodeItem[]>([])

onMounted(async () => {
  const result = await listNodes({ page: 1, page_size: 200 })
  nodeOptions.value = result.items
})

function statusLabel(status: PackageStatus): string {
  return PACKAGE_STATUS_MAP[status]?.label ?? status
}

function statusTag(status: PackageStatus): string {
  return PACKAGE_STATUS_MAP[status]?.tag ?? 'info'
}

function formatGoodsCodes(items?: PackageGoodsItem[]): string {
  if (!items?.length) return '—'
  return items.map((g) => g.goods_code).join('、')
}
</script>

<template>
  <div class="page-card">
    <PageToolbar title="包裹管理">
      <template #filters>
        <el-select
          v-model="filters.status"
          placeholder="包裹状态"
          clearable
          style="width: 130px"
          @change="applyFilters"
        >
          <el-option label="全部状态" value="" />
          <el-option
            v-for="opt in PACKAGE_STATUS_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-select
          v-model="filters.from_node_code"
          placeholder="起始节点"
          clearable
          filterable
          style="width: 170px"
          @change="applyFilters"
        >
          <el-option label="全部" value="" />
          <el-option
            v-for="node in nodeOptions"
            :key="`from-${node.node_code}`"
            :label="node.node_code"
            :value="node.node_code"
          />
        </el-select>
        <el-select
          v-model="filters.to_node_code"
          placeholder="目的节点"
          clearable
          filterable
          style="width: 170px"
          @change="applyFilters"
        >
          <el-option label="全部" value="" />
          <el-option
            v-for="node in nodeOptions"
            :key="`to-${node.node_code}`"
            :label="node.node_code"
            :value="node.node_code"
          />
        </el-select>
      </template>
    </PageToolbar>

    <DataTable :data="items" :loading="loading" stripe border>
      <el-table-column prop="package_code" label="包裹编号" min-width="140" />
      <el-table-column prop="weight" label="重量(kg)" width="90" />
      <el-table-column prop="volume" label="体积(m³)" width="90" />
      <el-table-column prop="from_node_code" label="起始节点" width="100" />
      <el-table-column prop="to_node_code" label="目的节点" width="100" />
      <el-table-column label="货物数" width="80">
        <template #default="{ row }">
          {{ row.goods_items?.length ?? 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="货物明细" min-width="180">
        <template #default="{ row }">
          <span class="goods-codes">
            {{ formatGoodsCodes(row.goods_items) }}
          </span>
        </template>
      </el-table-column>
    </DataTable>

    <TablePagination
      :total="total"
      :page="page"
      :page-size="pageSize"
      @update:page="onPageChange"
      @update:page-size="onSizeChange"
    />
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
}

.goods-codes {
  font-size: 12px;
  color: #606266;
}
</style>
