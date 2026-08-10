<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import DataTable from '@/components/crud/DataTable.vue'
import TablePagination from '@/components/crud/TablePagination.vue'
import { usePagedList } from '@/composables/usePagedList'
import { useExceptionReplan } from '@/composables/useExceptionReplan'
import { listGlobalSchedules } from '@/api/schedule'
import { listDispatchBatches } from '@/api/schedule'
import { listNodes } from '@/api/nodes'
import { listRoutes } from '@/api/routes'
import {
  createException,
  getException,
  listExceptions,
  resolveException,
} from '@/api/exceptions'
import EntityDetailDrawer from '@/components/detail/EntityDetailDrawer.vue'
import ExceptionDetailBody from '@/components/detail/ExceptionDetailBody.vue'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAuthStore } from '@/stores/auth'
import type {
  CreateExceptionPayload,
  ExceptionEvent,
  ExceptionStatus,
  ExceptionSubtype,
  ExceptionType,
  RecommendedAction,
} from '@/types/exception'
import type { GlobalScheduleSummary } from '@/types/schedule'
import type { NodeItem } from '@/types/node'
import type { RouteListItem } from '@/types/route'
import { formatDateTime } from '@/utils/format'

const authStore = useAuthStore()

const EXCEPTION_TYPE_OPTIONS: { label: string; value: ExceptionType }[] = [
  { label: '节点异常', value: 'node' },
  { label: '道路异常', value: 'road' },
]

const SUBTYPE_OPTIONS: Record<ExceptionType, { label: string; value: ExceptionSubtype }[]> = {
  node: [
    { label: '容量上限', value: 'capacity_limit' },
    { label: '存储超时', value: 'storage_timeout' },
    { label: '节点维修', value: 'node_maintenance' },
  ],
  road: [
    { label: '道路封闭', value: 'road_closed' },
    { label: '交通拥堵', value: 'congestion' },
    { label: '交通事故', value: 'road_accident' },
  ],
}

const ACTION_LABEL: Record<RecommendedAction, string> = {
  redispatch: '重新调度',
  reroute: '重新规划路径',
}

const STATUS_LABEL = {
  open: { label: '待处理', tag: 'danger' as const },
  resolved: { label: '已解决', tag: 'success' as const },
}

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
} = usePagedList<ExceptionEvent>((params) => listExceptions(params), {
  status: '',
  exception_type: '',
})

const { replanningCode, batchReplanning, runReplan, runBatchReplan } = useExceptionReplan(load)

const {
  visible: detailVisible,
  loading: detailLoading,
  data: detailData,
  title: detailTitle,
  open: openExceptionDetail,
} = useEntityDetail<ExceptionEvent>((code) => getException(code))

const resolvingCode = ref('')
const selectedRows = ref<ExceptionEvent[]>([])
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const scheduleOptions = ref<GlobalScheduleSummary[]>([])
const nodeOptions = ref<NodeItem[]>([])
const routeOptions = ref<RouteListItem[]>([])
const selectedBatchCode = ref('')
const routesLoading = ref(false)
const hasBatchForSchedule = ref(false)

const form = reactive<CreateExceptionPayload>({
  exception_type: 'node',
  exception_subtype: 'capacity_limit',
  target_type: 'node',
  target_code: '',
  recommended_action: 'redispatch',
  related_schedule_code: '',
  description: '',
})

const rules: FormRules = {
  exception_type: [{ required: true, message: '请选择异常类型', trigger: 'change' }],
  recommended_action: [{ required: true, message: '请选择推荐动作', trigger: 'change' }],
  related_schedule_code: [
    { required: true, message: '请选择关联调度方案', trigger: 'change' },
  ],
  description: [{ required: true, message: '请填写异常描述', trigger: 'blur' }],
  target_code: [
    {
      validator: (_rule, value, callback) => {
        if (form.recommended_action === 'reroute') {
          if (!value) {
            callback(new Error('reroute 须选择路线'))
            return
          }
        } else if (form.target_type === 'node' && !value) {
          callback(new Error('请选择节点'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

const subtypeOptions = computed(() => SUBTYPE_OPTIONS[form.exception_type])

function resetForm(): void {
  form.exception_type = 'node'
  form.exception_subtype = 'capacity_limit'
  form.target_type = 'node'
  form.target_code = ''
  form.recommended_action = 'redispatch'
  form.related_schedule_code = scheduleOptions.value[0]?.schedule_code ?? ''
  form.description = ''
  selectedBatchCode.value = ''
  routeOptions.value = []
  hasBatchForSchedule.value = false
}

function applyTypeDefaults(type: ExceptionType): void {
  if (type === 'node') {
    form.recommended_action = 'redispatch'
    form.target_type = 'node'
    form.exception_subtype = 'capacity_limit'
  } else {
    form.recommended_action = 'reroute'
    form.target_type = 'route'
    form.exception_subtype = 'road_closed'
    form.target_code = ''
  }
}

watch(
  () => form.exception_type,
  (type) => {
    applyTypeDefaults(type)
  },
)

async function loadRouteOptionsForSchedule(code: string): Promise<void> {
  form.target_code = ''
  routeOptions.value = []
  selectedBatchCode.value = ''
  hasBatchForSchedule.value = false
  if (!code || form.recommended_action !== 'reroute') return

  routesLoading.value = true
  try {
    const batches = await listDispatchBatches({
      schedule_code: code,
      page: 1,
      page_size: 10,
    })
    const batch = batches.items[0]
    if (!batch) return
    hasBatchForSchedule.value = true
    selectedBatchCode.value = batch.batch_code

    // MVP：路线在 F006 路径规划后才有（Dashboard 手动触发）；节点间调度暂不写 routes 表（见联调反馈 P2）
    const routes = await listRoutes({
      batch_code: batch.batch_code,
      page: 1,
      page_size: 100,
    })
    routeOptions.value = routes.items
    if (routes.items.length === 1) {
      form.target_code = routes.items[0].route_code
    }
  } catch (err) {
    ElMessage.warning(
      err instanceof Error ? err.message : '加载路线列表失败',
    )
  } finally {
    routesLoading.value = false
  }
}

watch(
  () =>
    [form.related_schedule_code, form.recommended_action, form.exception_type] as const,
  async ([code, action]) => {
    if (!code || action !== 'reroute') {
      routeOptions.value = []
      selectedBatchCode.value = ''
      hasBatchForSchedule.value = false
      return
    }
    await loadRouteOptionsForSchedule(code)
  },
)

async function loadFormOptions(): Promise<void> {
  const [schedules, nodes] = await Promise.all([
    listGlobalSchedules({ page: 1, page_size: 100 }),
    listNodes({ page: 1, page_size: 200 }),
  ])
  scheduleOptions.value = schedules.items
  nodeOptions.value = nodes.items
}

onMounted(() => {
  void loadFormOptions()
})

function openCreate(): void {
  resetForm()
  dialogVisible.value = true
}

async function submitForm(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await createException({
      ...form,
      target_type: form.recommended_action === 'reroute' ? 'route' : form.target_type,
    })
    ElMessage.success('异常已录入，相关订单/包裹可能已标记为异常状态')
    dialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '录入失败')
  } finally {
    submitting.value = false
  }
}

async function handleResolve(row: ExceptionEvent): Promise<void> {
  resolvingCode.value = row.event_code
  try {
    await resolveException(row.event_code)
    ElMessage.success('已标记为解决')
    await load()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    resolvingCode.value = ''
  }
}

/** 已选中的待处理事件编码（批量重规划只对 open 事件生效） */
const selectedOpenCodes = computed(() =>
  selectedRows.value.filter((r) => r.status === 'open').map((r) => r.event_code),
)

async function handleBatchReplan(): Promise<void> {
  await runBatchReplan(selectedOpenCodes.value)
}

function typeLabel(type: ExceptionType): string {
  return EXCEPTION_TYPE_OPTIONS.find((o) => o.value === type)?.label ?? type
}

function actionLabel(action: RecommendedAction): string {
  return ACTION_LABEL[action]
}

function statusInfo(status: ExceptionStatus) {
  return STATUS_LABEL[status]
}
</script>

<template>
  <div class="page-card">
    <PageToolbar title="异常管理">
      <template #filters>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          style="width: 120px"
          @change="applyFilters"
        >
          <el-option label="全部状态" value="" />
          <el-option label="待处理" value="open" />
          <el-option label="已解决" value="resolved" />
        </el-select>
        <el-select
          v-model="filters.exception_type"
          placeholder="异常类型"
          clearable
          style="width: 130px"
          @change="applyFilters"
        >
          <el-option label="全部类型" value="" />
          <el-option
            v-for="opt in EXCEPTION_TYPE_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </template>
      <template #actions>
        <el-button
          v-if="authStore.isDispatcher"
          type="warning"
          :loading="batchReplanning"
          :disabled="selectedOpenCodes.length === 0"
          @click="handleBatchReplan"
        >
          批量重规划{{ selectedOpenCodes.length ? `（${selectedOpenCodes.length}）` : '' }}
        </el-button>
        <el-button v-if="authStore.isDispatcher" type="primary" @click="openCreate">
          录入异常
        </el-button>
      </template>
    </PageToolbar>

    <DataTable
      :data="items"
      :loading="loading"
      stripe
      border
      @selection-change="(rows: ExceptionEvent[]) => (selectedRows = rows)"
    >
      <el-table-column type="selection" width="42" />
      <el-table-column prop="event_code" label="事件编号" min-width="150" />
      <el-table-column prop="exception_type" label="类型" width="100">
        <template #default="{ row }">
          {{ typeLabel(row.exception_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="target_code" label="目标" min-width="120">
        <template #default="{ row }">
          <span v-if="row.target_type">{{ row.target_type }}:</span>
          {{ row.target_code || '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="recommended_action" label="推荐动作" width="120">
        <template #default="{ row }">
          <el-tag type="warning" size="small">
            {{ actionLabel(row.recommended_action) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="related_schedule_code" label="关联方案" min-width="140" />
      <el-table-column prop="replan_batch_code" label="重规划批次" min-width="130">
        <template #default="{ row }">
          {{ row.replan_batch_code || '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusInfo(row.status).tag" size="small">
            {{ statusInfo(row.status).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        label="描述"
        min-width="160"
        show-overflow-tooltip
      />
      <el-table-column prop="created_at" label="创建时间" min-width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            @click="openExceptionDetail(row.event_code, `异常 · ${row.event_code}`)"
          >
            查看
          </el-button>
          <template v-if="authStore.isDispatcher && row.status === 'open'">
            <el-button
              type="primary"
              link
              :loading="replanningCode === row.event_code"
              :disabled="Boolean(replanningCode && replanningCode !== row.event_code)"
              @click="runReplan(row)"
            >
              触发重规划
            </el-button>
            <el-button
              type="success"
              link
              :loading="resolvingCode === row.event_code"
              @click="handleResolve(row)"
            >
              标记已解决
            </el-button>
          </template>
        </template>
      </el-table-column>
    </DataTable>

    <TablePagination
      :total="total"
      :page="page"
      :page-size="pageSize"
      @page-change="onPageChange"
      @size-change="onSizeChange"
    />

    <el-dialog v-model="dialogVisible" title="录入异常" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="异常类型" prop="exception_type">
          <el-select v-model="form.exception_type" style="width: 100%">
            <el-option
              v-for="opt in EXCEPTION_TYPE_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="子类型">
          <el-select v-model="form.exception_subtype" style="width: 100%">
            <el-option
              v-for="opt in subtypeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="推荐动作" prop="recommended_action">
          <el-select v-model="form.recommended_action" style="width: 100%">
            <el-option label="重新调度 (redispatch)" value="redispatch" />
            <el-option label="重新规划路径 (reroute)" value="reroute" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联方案" prop="related_schedule_code">
          <el-select
            v-model="form.related_schedule_code"
            filterable
            placeholder="选择全局调度方案"
            style="width: 100%"
          >
            <el-option
              v-for="s in scheduleOptions"
              :key="s.schedule_code"
              :label="`${s.schedule_code}${s.version ? ` (v${s.version})` : ''}`"
              :value="s.schedule_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="form.recommended_action === 'redispatch'"
          label="目标节点"
          prop="target_code"
        >
          <el-select
            v-model="form.target_code"
            filterable
            clearable
            placeholder="选择节点"
            style="width: 100%"
          >
            <el-option
              v-for="node in nodeOptions"
              :key="node.node_code"
              :label="`${node.node_code} (${node.name})`"
              :value="node.node_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-else
          label="目标路线"
          prop="target_code"
        >
          <el-select
            v-model="form.target_code"
            filterable
            :loading="routesLoading"
            placeholder="选择路线（需已完成节点间调度）"
            style="width: 100%"
            :disabled="routesLoading || !routeOptions.length"
          >
            <el-option
              v-for="route in routeOptions"
              :key="route.route_code"
              :label="route.route_code"
              :value="route.route_code"
            />
          </el-select>
          <p
            v-if="form.related_schedule_code && !routesLoading && !routeOptions.length"
            class="form-hint"
          >
            <template v-if="!hasBatchForSchedule">
              该方案尚无调度批次，请先在调度工作台完成节点间调度
            </template>
            <template v-else>
              请先在调度工作台对该批次点击「路径规划」生成路线（MVP 暂不在节点间调度时自动产线）
            </template>
          </p>
        </el-form-item>
        <el-form-item label="异常描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="描述异常情况"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          提交
        </el-button>
      </template>
    </el-dialog>

    <EntityDetailDrawer
      v-model="detailVisible"
      :title="detailTitle"
      :loading="detailLoading"
    >
      <ExceptionDetailBody v-if="detailData" :data="detailData" />
    </EntityDetailDrawer>
  </div>
</template>

<style scoped>
.form-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #e6a23c;
}
</style>
