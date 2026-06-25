<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useArrivalConfirm } from '@/composables/useArrivalConfirm'
import { useAuthStore } from '@/stores/auth'
import { useMockSimulation } from '@/utils/env'
import { ARRIVAL_EXCEPTION_SUBTYPE_OPTIONS } from '@/constants/arrival'

const authStore = useAuthStore()
const router = useRouter()
const mockMode = useMockSimulation()

const {
  schedules,
  nodes,
  scheduleCode,
  nodeCode,
  packages,
  selections,
  lastResult,
  listLoading,
  nodesLoading,
  fetchLoading,
  submitLoading,
  initLoading,
  canSubmit,
  loadSchedules,
  loadNodes,
  initDemoData,
  fetchPackages,
  submit,
} = useArrivalConfirm()

onMounted(async () => {
  await loadSchedules()
  await loadNodes()
})

watch(scheduleCode, () => {
  loadNodes()
})

function formatGoods(items: { goods_code: string; order_code?: string; goods_name?: string }[]): string {
  return items
    .map((g) => `${g.goods_code}${g.goods_name ? `（${g.goods_name}）` : ''}${g.order_code ? ` / ${g.order_code}` : ''}`)
    .join('；')
}

function goDashboard(): void {
  router.push('/dashboard')
}
</script>

<template>
  <div class="arrival-page">
    <el-card class="page-card" shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <h2 class="page-title">节点到货确认</h2>
            <p class="page-desc">
              选择调度方案与 L1 分拣中心，确认到站包裹正常或异常；异常将级联影响下游预生成包裹。
            </p>
          </div>
        </div>
      </template>

      <el-alert
        v-if="!authStore.isDispatcher"
        type="warning"
        show-icon
        :closable="false"
        title="仅调度员可执行到站确认操作"
        class="role-alert"
      />

      <div v-if="authStore.isDispatcher" class="filter-bar">
        <el-select
          v-model="scheduleCode"
          placeholder="选择调度方案"
          filterable
          :loading="listLoading"
          style="width: 260px"
        >
          <el-option
            v-for="s in schedules"
            :key="s.schedule_code"
            :label="s.schedule_code"
            :value="s.schedule_code"
          />
        </el-select>

        <el-select
          v-model="nodeCode"
          placeholder="选择 L1 分拣中心"
          filterable
          :loading="nodesLoading"
          style="width: 260px"
        >
          <el-option
            v-for="n in nodes"
            :key="n.node_code"
            :label="`${n.name}（${n.node_code}）`"
            :value="n.node_code"
          />
        </el-select>

        <el-button type="primary" :loading="fetchLoading" @click="fetchPackages">
          加载待确认包裹
        </el-button>

        <el-button
          v-if="mockMode"
          :loading="initLoading"
          @click="initDemoData"
        >
          初始化演示数据
        </el-button>
      </div>

      <el-table
        v-if="authStore.isDispatcher && packages.length > 0"
        v-loading="fetchLoading"
        :data="packages"
        border
        stripe
        class="package-table"
      >
        <el-table-column prop="package_code" label="包裹号" width="160" />
        <el-table-column label="起终点" min-width="200">
          <template #default="{ row }">
            {{ row.from_node_code }} → {{ row.to_node_code }}
          </template>
        </el-table-column>
        <el-table-column prop="level_phase" label="阶段" width="80">
          <template #default="{ row }">
            L{{ row.level_phase ?? 0 }}
          </template>
        </el-table-column>
        <el-table-column label="货物" min-width="220">
          <template #default="{ row }">
            {{ formatGoods(row.goods_items) }}
          </template>
        </el-table-column>
        <el-table-column label="确认结果" width="180">
          <template #default="{ row }">
            <el-radio-group v-model="selections[row.package_code].result">
              <el-radio value="normal">正常</el-radio>
              <el-radio value="exception">异常</el-radio>
            </el-radio-group>
          </template>
        </el-table-column>
        <el-table-column label="异常说明" min-width="280">
          <template #default="{ row }">
            <div
              v-if="selections[row.package_code].result === 'exception'"
              class="exception-fields"
            >
              <el-select
                v-model="selections[row.package_code].exception_subtype"
                placeholder="异常类型"
                clearable
                style="width: 120px"
              >
                <el-option
                  v-for="opt in ARRIVAL_EXCEPTION_SUBTYPE_OPTIONS"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
              <el-input
                v-model="selections[row.package_code].remark"
                placeholder="备注（可选）"
                clearable
              />
            </div>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-else-if="authStore.isDispatcher && !fetchLoading"
        description="请选择方案与节点后加载待确认包裹"
      />

      <div v-if="authStore.isDispatcher && packages.length > 0" class="submit-bar">
        <el-button
          type="primary"
          size="large"
          :loading="submitLoading"
          :disabled="!canSubmit"
          @click="submit"
        >
          确认到站
        </el-button>
      </div>

      <el-card
        v-if="lastResult"
        class="result-card enhance-panel"
        shadow="never"
      >
        <template #header>
          <span>确认结果摘要</span>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="正常包裹">
            {{ lastResult.normal_packages.join('、') || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="异常包裹">
            {{ lastResult.exception_packages.join('、') || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="级联激活（packed）">
            {{ lastResult.activated_downstream_packages.join('、') || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="级联异常">
            {{ lastResult.cascade_exception_packages.join('、') || '无' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="lastResult.updated_goods.length" label="货物状态">
            <span
              v-for="(g, idx) in lastResult.updated_goods"
              :key="g.goods_code ?? idx"
            >
              {{ g.goods_code }}→{{ g.status }}
              <template v-if="idx < lastResult.updated_goods.length - 1">；</template>
            </span>
          </el-descriptions-item>
          <el-descriptions-item v-if="lastResult.updated_orders.length" label="订单状态">
            <span
              v-for="(o, idx) in lastResult.updated_orders"
              :key="o.order_code ?? idx"
            >
              {{ o.order_code }}→{{ o.status }}
              <template v-if="idx < lastResult.updated_orders.length - 1">；</template>
            </span>
          </el-descriptions-item>
        </el-descriptions>
        <div class="next-step">
          <span>下一步可前往调度工作台执行 L1→L2 节点间调度或模拟送达。</span>
          <el-button type="primary" link @click="goDashboard">打开调度工作台</el-button>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<style scoped>
.arrival-page {
  max-width: 1200px;
}

.page-card {
  border-radius: 8px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 600;
}

.page-desc {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.role-alert {
  margin-bottom: 16px;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.package-table {
  margin-bottom: 16px;
}

.exception-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.text-muted {
  color: var(--el-text-color-secondary);
}

.submit-bar {
  margin-bottom: 20px;
}

.result-card {
  margin-top: 8px;
}

.next-step {
  margin-top: 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
