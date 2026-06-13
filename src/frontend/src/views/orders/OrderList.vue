<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadRequestOptions } from 'element-plus'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import { listLevel0SortingCenters } from '@/api/nodes'
import {
  createOrder,
  deleteOrder,
  importOrders,
  listOrders,
  updateOrder,
} from '@/api/orders'
import { ORDER_STATUS_MAP, ORDER_STATUS_OPTIONS } from '@/constants/status'
import { useAuthStore } from '@/stores/auth'
import type { NodeItem } from '@/types/node'
import type { Order, OrderCreatePayload, OrderGoodsCreateItem, OrderStatus } from '@/types/order'
import { formatDateTime } from '@/utils/format'

const authStore = useAuthStore()

const {
  items,
  total,
  page,
  pageSize,
  loading,
  filters,
  load,
  onPageChange,
  onSizeChange,
  applyFilters,
} = usePagedList<Order>((params) => listOrders(params), { status: '' })

const destinationOptions = ref<NodeItem[]>([])

onMounted(async () => {
  destinationOptions.value = await listLevel0SortingCenters()
})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const importing = ref(false)
const formRef = ref<FormInstance>()
const editingCode = ref('')

const form = reactive({
  order_code: '',
  destination_node_code: '',
  time_window: '',
})

const goodsItems = ref<OrderGoodsCreateItem[]>([
  { goods_name: '', goods_type: '电子产品', weight: 1, volume: 0.01 },
])

const rules: FormRules = {
  destination_node_code: [
    { required: true, message: '请选择目的地', trigger: 'change' },
  ],
  time_window: [{ required: true, message: '请输入时效要求', trigger: 'blur' }],
}

function resetForm(): void {
  form.order_code = ''
  form.destination_node_code = ''
  form.time_window = '09:00-12:00'
  goodsItems.value = [
    { goods_name: '', goods_type: '电子产品', weight: 1, volume: 0.01 },
  ]
}

function addGoodsRow(): void {
  goodsItems.value.push({
    goods_name: '',
    goods_type: '电子产品',
    weight: 1,
    volume: 0.01,
  })
}

function removeGoodsRow(index: number): void {
  if (goodsItems.value.length <= 1) {
    ElMessage.warning('至少保留一条货物')
    return
  }
  goodsItems.value.splice(index, 1)
}

function validateGoods(): boolean {
  for (const [i, item] of goodsItems.value.entries()) {
    if (!item.goods_name.trim()) {
      ElMessage.warning(`请填写第 ${i + 1} 条货物名称`)
      return false
    }
    if (item.weight <= 0 || item.volume <= 0) {
      ElMessage.warning(`第 ${i + 1} 条货物重量和体积须大于 0`)
      return false
    }
  }
  return true
}

function openCreate(): void {
  dialogMode.value = 'create'
  editingCode.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Order): void {
  if (row.status !== 'pending') return
  dialogMode.value = 'edit'
  editingCode.value = row.order_code
  form.order_code = row.order_code
  form.destination_node_code = row.destination_node_code
  form.time_window = row.time_window
  dialogVisible.value = true
}

async function submitForm(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (dialogMode.value === 'create' && !validateGoods()) return

  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      const payload: OrderCreatePayload = {
        order_code: form.order_code || undefined,
        destination_node_code: form.destination_node_code,
        time_window: form.time_window,
        goods: goodsItems.value.map((g) => ({
          goods_name: g.goods_name.trim(),
          goods_type: g.goods_type,
          weight: g.weight,
          volume: g.volume,
        })),
      }
      await createOrder(payload)
      ElMessage.success('新增成功')
    } else {
      await updateOrder(editingCode.value, {
        destination_node_code: form.destination_node_code,
        time_window: form.time_window,
      })
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: Order): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定删除订单 ${row.order_code}？`, '确认删除', {
      type: 'warning',
    })
    await deleteOrder(row.order_code)
    ElMessage.success('删除成功')
    await load()
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}

async function handleImport(options: UploadRequestOptions): Promise<void> {
  importing.value = true
  try {
    const result = await importOrders(options.file as File)
    ElMessage.success(
      `导入完成：成功 ${result.success_count} 条，失败 ${result.fail_count} 条`,
    )
    await load()
    options.onSuccess?.(result)
  } catch (e) {
    const msg = e instanceof Error ? e.message : '导入失败'
    ElMessage.error(msg)
  } finally {
    importing.value = false
  }
}

function statusLabel(status: OrderStatus): string {
  return ORDER_STATUS_MAP[status]?.label ?? status
}

function statusTag(status: OrderStatus): string {
  return ORDER_STATUS_MAP[status]?.tag ?? 'info'
}
</script>

<template>
  <div class="page-card">
    <PageToolbar title="订单管理">
      <template #filters>
        <el-select
          v-model="filters.status"
          placeholder="订单状态"
          clearable
          style="width: 140px"
          @change="applyFilters"
        >
          <el-option label="全部状态" value="" />
          <el-option
            v-for="opt in ORDER_STATUS_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </template>
      <template #actions>
        <el-upload
          v-if="authStore.isDispatcher"
          :show-file-list="false"
          :http-request="handleImport"
          accept=".xlsx,.xls,.csv"
        >
          <el-button :loading="importing">Excel 导入</el-button>
        </el-upload>
        <el-button v-if="authStore.isDispatcher" type="primary" @click="openCreate">
          新增订单
        </el-button>
      </template>
    </PageToolbar>

    <DataTable :data="items" :loading="loading" stripe border>
      <el-table-column prop="order_code" label="订单编号" min-width="140" />
      <el-table-column
        prop="destination_node_name"
        label="目的地（0级分拣）"
        min-width="160"
      >
        <template #default="{ row }">
          {{ row.destination_node_name || row.destination_node_code }}
        </template>
      </el-table-column>
      <el-table-column prop="time_window" label="时效要求" width="120" />
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
      <el-table-column
        v-if="authStore.isDispatcher"
        label="操作"
        width="140"
        fixed="right"
      >
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
          <span v-else class="text-muted">—</span>
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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增订单' : '编辑订单'"
      :width="dialogMode === 'create' ? '640px' : '480px'"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item v-if="dialogMode === 'create'" label="订单编号">
          <el-input
            v-model="form.order_code"
            placeholder="留空则自动生成"
          />
        </el-form-item>
        <el-form-item label="目的地" prop="destination_node_code">
          <el-select
            v-model="form.destination_node_code"
            placeholder="选择 0 级分拣中心"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="node in destinationOptions"
              :key="node.node_code"
              :label="`${node.name}（${node.node_code}）`"
              :value="node.node_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时效要求" prop="time_window">
          <el-input v-model="form.time_window" placeholder="如 09:00-12:00" />
        </el-form-item>
        <template v-if="dialogMode === 'create'">
          <el-divider content-position="left">货物明细（至少 1 条）</el-divider>
          <div
            v-for="(item, index) in goodsItems"
            :key="index"
            class="goods-row"
          >
            <el-form-item label="名称" label-width="60px" class="goods-field">
              <el-input v-model="item.goods_name" placeholder="货物名称" />
            </el-form-item>
            <el-form-item label="类型" label-width="60px" class="goods-field">
              <el-input v-model="item.goods_type" placeholder="货物类型" />
            </el-form-item>
            <el-form-item label="重量" label-width="60px" class="goods-field-sm">
              <el-input-number v-model="item.weight" :min="0.01" :step="0.1" />
            </el-form-item>
            <el-form-item label="体积" label-width="60px" class="goods-field-sm">
              <el-input-number v-model="item.volume" :min="0.01" :step="0.01" />
            </el-form-item>
            <el-button
              type="danger"
              link
              class="goods-remove"
              @click="removeGoodsRow(index)"
            >
              删除
            </el-button>
          </div>
          <el-button type="primary" link @click="addGoodsRow">+ 添加货物</el-button>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
}

.text-muted {
  color: #c0c4cc;
}

.goods-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #ebeef5;
}

.goods-field {
  flex: 1 1 180px;
  margin-bottom: 0;
}

.goods-field-sm {
  flex: 0 1 140px;
  margin-bottom: 0;
}

.goods-remove {
  margin-top: 8px;
}
</style>
