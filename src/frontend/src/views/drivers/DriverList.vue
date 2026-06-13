<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import { listDrivers } from '@/api/drivers'
import { listNodes } from '@/api/nodes'
import { DRIVER_STATUS_MAP, DRIVER_STATUS_OPTIONS } from '@/constants/status'
import type { Driver, DriverStatus } from '@/types/driver'
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
} = usePagedList<Driver>((params) => listDrivers(params), {
  status: '',
  node_code: '',
})

const nodeOptions = ref<NodeItem[]>([])

onMounted(async () => {
  const result = await listNodes({ page: 1, page_size: 200 })
  nodeOptions.value = result.items
})

function statusLabel(status: DriverStatus): string {
  return DRIVER_STATUS_MAP[status]?.label ?? status
}

function statusTag(status: DriverStatus): string {
  return DRIVER_STATUS_MAP[status]?.tag ?? 'info'
}
</script>

<template>
  <div class="page-card">
    <PageToolbar title="司机管理">
      <template #filters>
        <el-select
          v-model="filters.status"
          placeholder="司机状态"
          clearable
          style="width: 120px"
          @change="applyFilters"
        >
          <el-option label="全部状态" value="" />
          <el-option
            v-for="opt in DRIVER_STATUS_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-select
          v-model="filters.node_code"
          placeholder="所属节点"
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
      </template>
    </PageToolbar>

    <DataTable :data="items" :loading="loading" stripe border>
      <el-table-column prop="driver_code" label="司机编号" min-width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="phone" label="电话" min-width="120" />
      <el-table-column prop="license_type" label="驾照类型" width="90" />
      <el-table-column prop="shift" label="班次" min-width="150" />
      <el-table-column prop="node_code" label="所属节点" width="100" />
      <el-table-column prop="status" label="状态" width="90">
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
