<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import { listNodes } from '@/api/nodes'
import {
  createVehicle,
  deleteVehicle,
  listVehicles,
  suggestVehicleCode,
  updateVehicle,
} from '@/api/vehicles'
import {
  ENERGY_TYPE_OPTIONS,
  VEHICLE_STATUS_MAP,
  VEHICLE_STATUS_OPTIONS,
} from '@/constants/status'
import { useAuthStore } from '@/stores/auth'
import type { NodeItem } from '@/types/node'
import type { Vehicle, VehicleStatus } from '@/types/vehicle'

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
} = usePagedList<Vehicle>((params) => listVehicles(params), {
  node_code: '',
  status: '',
})

const nodeOptions = ref<NodeItem[]>([])

onMounted(async () => {
  const result = await listNodes({ page: 1, page_size: 200 })
  nodeOptions.value = result.items
})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingCode = ref('')

const form = reactive({
  vehicle_code: '',
  model: '',
  capacity: 2.0,
  energy_type: 'electric',
  vehicle_type: 'normal',
  status: 'idle' as VehicleStatus,
  node_code: '',
  last_arrived_node_code: '',
})

const rules: FormRules = {
  vehicle_code: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  model: [{ required: true, message: '请输入车型', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入载重', trigger: 'blur' }],
  energy_type: [{ required: true, message: '请选择能源类型', trigger: 'change' }],
  node_code: [{ required: true, message: '请选择所属节点', trigger: 'change' }],
  last_arrived_node_code: [
    { required: true, message: '请选择最后到达节点', trigger: 'change' },
  ],
}

function resetForm(): void {
  form.vehicle_code = suggestVehicleCode(items.value)
  form.model = ''
  form.capacity = 2.0
  form.energy_type = 'electric'
  form.vehicle_type = 'normal'
  form.status = 'idle'
  form.node_code = nodeOptions.value[0]?.node_code ?? ''
  form.last_arrived_node_code = nodeOptions.value[0]?.node_code ?? ''
}

function openCreate(): void {
  dialogMode.value = 'create'
  editingCode.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Vehicle): void {
  dialogMode.value = 'edit'
  editingCode.value = row.vehicle_code
  form.vehicle_code = row.vehicle_code
  form.model = row.model
  form.capacity = row.capacity
  form.energy_type = row.energy_type
  form.vehicle_type = row.vehicle_type
  form.status = row.status
  form.node_code = row.node_code
  form.last_arrived_node_code = row.last_arrived_node_code
  dialogVisible.value = true
}

async function submitForm(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      vehicle_code: form.vehicle_code,
      model: form.model,
      capacity: form.capacity,
      energy_type: form.energy_type,
      vehicle_type: form.vehicle_type,
      status: form.status,
      node_code: form.node_code,
      last_arrived_node_code: form.last_arrived_node_code,
    }
    if (dialogMode.value === 'create') {
      await createVehicle(payload)
      ElMessage.success('新增成功')
    } else {
      await updateVehicle(editingCode.value, payload)
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

async function handleDelete(row: Vehicle): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定删除车辆 ${row.vehicle_code}？`, '确认删除', {
      type: 'warning',
    })
    await deleteVehicle(row.vehicle_code)
    ElMessage.success('删除成功')
    await load()
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}

function energyLabel(value: string): string {
  return ENERGY_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value
}

function statusLabel(status: VehicleStatus): string {
  return VEHICLE_STATUS_MAP[status]?.label ?? status
}

function statusTag(status: VehicleStatus): string {
  return VEHICLE_STATUS_MAP[status]?.tag ?? 'info'
}
</script>

<template>
  <div class="page-card">
    <PageToolbar title="车辆管理">
      <template #filters>
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
        <el-select
          v-model="filters.status"
          placeholder="车辆状态"
          clearable
          style="width: 120px"
          @change="applyFilters"
        >
          <el-option label="全部状态" value="" />
          <el-option
            v-for="opt in VEHICLE_STATUS_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </template>
      <template #actions>
        <el-button v-if="authStore.isDispatcher" type="primary" @click="openCreate">
          新增车辆
        </el-button>
      </template>
    </PageToolbar>

    <DataTable :data="items" :loading="loading" stripe border>
      <el-table-column prop="vehicle_code" label="车牌号" min-width="110" />
      <el-table-column prop="model" label="车型" min-width="120" />
      <el-table-column prop="capacity" label="载重(t)" width="90" />
      <el-table-column prop="energy_type" label="能源" width="80">
        <template #default="{ row }">
          {{ energyLabel(row.energy_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="node_code" label="所属节点" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="last_arrived_node_code"
        label="最后到达节点"
        width="120"
      />
      <el-table-column
        v-if="authStore.isDispatcher"
        label="操作"
        width="140"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button
            type="danger"
            link
            :disabled="row.status === 'delivering'"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
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
      :title="dialogMode === 'create' ? '新增车辆' : '编辑车辆'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="车牌号" prop="vehicle_code">
          <el-input
            v-model="form.vehicle_code"
            :disabled="dialogMode === 'edit'"
          />
        </el-form-item>
        <el-form-item label="车型" prop="model">
          <el-input v-model="form.model" placeholder="如 轻卡4.2米" />
        </el-form-item>
        <el-form-item label="载重(t)" prop="capacity">
          <el-input-number v-model="form.capacity" :min="0.1" :step="0.5" />
        </el-form-item>
        <el-form-item label="能源类型" prop="energy_type">
          <el-select v-model="form.energy_type" style="width: 100%">
            <el-option
              v-for="opt in ENERGY_TYPE_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属节点" prop="node_code">
          <el-select v-model="form.node_code" filterable style="width: 100%">
            <el-option
              v-for="node in nodeOptions"
              :key="node.node_code"
              :label="`${node.name}（${node.node_code}）`"
              :value="node.node_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="最后到达" prop="last_arrived_node_code">
          <el-select
            v-model="form.last_arrived_node_code"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="node in nodeOptions"
              :key="node.node_code"
              :label="`${node.name}（${node.node_code}）`"
              :value="node.node_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogMode === 'edit'" label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option
              v-for="opt in VEHICLE_STATUS_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
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
</style>
