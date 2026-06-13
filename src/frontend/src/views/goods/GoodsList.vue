<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import { listGoods } from '@/api/goods'
import { listNodes } from '@/api/nodes'
import { GOODS_STATUS_MAP, GOODS_STATUS_OPTIONS } from '@/constants/status'
import type { Goods, GoodsStatus } from '@/types/goods'
import type { NodeItem } from '@/types/node'
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
} = usePagedList<Goods>((params) => listGoods(params), {
  status: '',
  order_code: '',
  node_code: '',
})

const nodeOptions = ref<NodeItem[]>([])

onMounted(async () => {
  const result = await listNodes({ page: 1, page_size: 200 })
  nodeOptions.value = result.items.filter(
    (n) => n.node_type === 'storage_center',
  )
})

function statusLabel(status: GoodsStatus): string {
  return GOODS_STATUS_MAP[status]?.label ?? status
}

function statusTag(status: GoodsStatus): string {
  return GOODS_STATUS_MAP[status]?.tag ?? 'info'
}
</script>

<template>
  <div class="page-card">
    <PageToolbar title="货物管理">
      <template #filters>
        <el-select
          v-model="filters.status"
          placeholder="货物状态"
          clearable
          style="width: 130px"
          @change="applyFilters"
        >
          <el-option label="全部状态" value="" />
          <el-option
            v-for="opt in GOODS_STATUS_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-select
          v-model="filters.node_code"
          placeholder="所在节点"
          clearable
          filterable
          style="width: 180px"
          @change="applyFilters"
        >
          <el-option label="全部节点" value="" />
          <el-option
            v-for="node in nodeOptions"
            :key="node.node_code"
            :label="`${node.name}（${node.node_code}）`"
            :value="node.node_code"
          />
        </el-select>
        <el-input
          v-model="filters.order_code"
          placeholder="订单编号"
          clearable
          style="width: 160px"
          @clear="applyFilters"
          @keyup.enter="applyFilters"
        />
        <el-button @click="applyFilters">查询</el-button>
      </template>
    </PageToolbar>

    <DataTable :data="items" :loading="loading" stripe border>
      <el-table-column prop="goods_code" label="货物编号" min-width="130" />
      <el-table-column prop="goods_name" label="名称" min-width="120" />
      <el-table-column prop="goods_type" label="类型" width="100" />
      <el-table-column prop="weight" label="重量(kg)" width="90" />
      <el-table-column prop="volume" label="体积(m³)" width="90" />
      <el-table-column prop="node_code" label="所在节点" width="100" />
      <el-table-column prop="order_code" label="所属订单" min-width="130" />
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
</style>
