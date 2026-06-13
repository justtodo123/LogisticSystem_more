<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import {
  createSortingCenter,
  createStorageCenter,
  deleteSortingCenter,
  deleteStorageCenter,
  listNodes,
  updateSortingCenter,
  updateStorageCenter,
} from '@/api/nodes'
import { useAuthStore } from '@/stores/auth'
import type { NodeItem, NodeType } from '@/types/node'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const authStore = useAuthStore()

const nodeType = computed(
  () => route.meta.nodeType as NodeType,
)
const pageTitle = computed(() =>
  nodeType.value === 'storage_center' ? '存储中心' : '分拣中心',
)
const isStorage = computed(() => nodeType.value === 'storage_center')

const {
  items,
  total,
  page,
  pageSize,
  loading,
  load,
  onPageChange,
  onSizeChange,
} = usePagedList<NodeItem>((params) =>
  listNodes({ ...params, node_type: nodeType.value }),
)

watch(nodeType, () => {
  page.value = 1
  load()
})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingCode = ref('')

const form = reactive({
  node_code: '',
  name: '',
  location: '',
  latitude: 30.5,
  longitude: 114.3,
  capacity: 1000,
  inventory: 0,
  level: 0,
  max_storage_time: 24,
})

const rules = computed<FormRules>(() => ({
  node_code: [{ required: true, message: '请输入节点编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  location: [{ required: true, message: '请输入地址', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }],
  level: [{ required: true, message: '请选择层级', trigger: 'change' }],
}))

function resetForm(): void {
  form.node_code = ''
  form.name = ''
  form.location = ''
  form.latitude = 30.5
  form.longitude = 114.3
  form.capacity = 1000
  form.inventory = 0
  form.level = isStorage.value ? 0 : 0
  form.max_storage_time = 24
}

function openCreate(): void {
  dialogMode.value = 'create'
  editingCode.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: NodeItem): void {
  dialogMode.value = 'edit'
  editingCode.value = row.node_code
  form.node_code = row.node_code
  form.name = row.name
  form.location = row.location
  form.latitude = row.latitude
  form.longitude = row.longitude
  form.capacity = row.capacity ?? 1000
  form.inventory = row.inventory ?? 0
  form.level = row.level ?? 0
  form.max_storage_time = row.max_storage_time ?? 24
  dialogVisible.value = true
}

async function submitForm(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isStorage.value) {
      const payload = {
        node_code: form.node_code,
        name: form.name,
        location: form.location,
        latitude: form.latitude,
        longitude: form.longitude,
        capacity: form.capacity,
        inventory: form.inventory,
      }
      if (dialogMode.value === 'create') {
        await createStorageCenter(payload)
        ElMessage.success('新增成功')
      } else {
        await updateStorageCenter(editingCode.value, payload)
        ElMessage.success('更新成功')
      }
    } else {
      const payload = {
        node_code: form.node_code,
        name: form.name,
        location: form.location,
        latitude: form.latitude,
        longitude: form.longitude,
        level: form.level,
        capacity: form.capacity,
        max_storage_time: form.max_storage_time,
      }
      if (dialogMode.value === 'create') {
        await createSortingCenter(payload)
        ElMessage.success('新增成功')
      } else {
        await updateSortingCenter(editingCode.value, payload)
        ElMessage.success('更新成功')
      }
    }
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: NodeItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定删除节点 ${row.node_code}？`, '确认删除', {
      type: 'warning',
    })
    if (isStorage.value) {
      await deleteStorageCenter(row.node_code)
    } else {
      await deleteSortingCenter(row.node_code)
    }
    ElMessage.success('删除成功')
    await load()
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}
</script>

<template>
  <div class="page-card">
    <PageToolbar :title="pageTitle">
      <template #actions>
        <el-button v-if="authStore.isDispatcher" type="primary" @click="openCreate">
          新增
        </el-button>
      </template>
    </PageToolbar>

    <DataTable :data="items" :loading="loading" stripe border>
      <el-table-column prop="node_code" label="节点编号" min-width="120" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="location" label="地址" min-width="200" show-overflow-tooltip />
      <template v-if="isStorage">
        <el-table-column prop="capacity" label="容量" width="100" />
        <el-table-column prop="inventory" label="库存" width="100" />
      </template>
      <template v-else>
        <el-table-column prop="level" label="层级" width="80">
          <template #default="{ row }">
            {{ row.level === 1 ? '1级' : '0级' }}
          </template>
        </el-table-column>
        <el-table-column prop="capacity" label="容量" width="100" />
        <el-table-column prop="max_storage_time" label="最大存储(h)" width="120" />
      </template>
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
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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
      :title="dialogMode === 'create' ? `新增${pageTitle}` : `编辑${pageTitle}`"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="节点编号" prop="node_code">
          <el-input
            v-model="form.node_code"
            :disabled="dialogMode === 'edit'"
            placeholder="如 SC006 / SO006"
          />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="地址" prop="location">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="form.latitude" :step="0.01" :precision="2" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="form.longitude" :step="0.01" :precision="2" />
        </el-form-item>
        <template v-if="isStorage">
          <el-form-item label="容量" prop="capacity">
            <el-input-number v-model="form.capacity" :min="1" />
          </el-form-item>
          <el-form-item label="库存">
            <el-input-number v-model="form.inventory" :min="0" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="层级" prop="level">
            <el-select v-model="form.level" style="width: 100%">
              <el-option :value="0" label="0级（快递站）" />
              <el-option :value="1" label="1级（物流中心）" />
            </el-select>
          </el-form-item>
          <el-form-item label="容量" prop="capacity">
            <el-input-number v-model="form.capacity" :min="1" />
          </el-form-item>
          <el-form-item label="最大存储(h)">
            <el-input-number v-model="form.max_storage_time" :min="1" />
          </el-form-item>
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
</style>
