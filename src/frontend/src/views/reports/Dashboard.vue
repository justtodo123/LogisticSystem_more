<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getReportOverview } from '@/api/reports'
import type { ReportOverview } from '@/types/report'
import SlaGauge from '@/components/charts/SlaGauge.vue'
import CostTrend from '@/components/charts/CostTrend.vue'
import ExceptionPie from '@/components/charts/ExceptionPie.vue'

const loading = ref(false)
const overview = ref<ReportOverview | null>(null)
const dateRange = ref<[string, string] | null>(null)

/** 将 el-date-picker 的 Date[] 转为 YYYY-MM-DD */
function toIsoDate(d: Date): string {
  const y = d.getFullYear()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function loadOverview(): Promise<void> {
  loading.value = true
  try {
    const [dateFrom, dateTo] = dateRange.value ?? [undefined, undefined]
    overview.value = await getReportOverview(dateFrom, dateTo)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '报表数据加载失败')
  } finally {
    loading.value = false
  }
}

function onDateRangeChange(value: [Date, Date] | null): void {
  if (value && value.length === 2) {
    dateRange.value = [toIsoDate(value[0]), toIsoDate(value[1])]
  } else {
    dateRange.value = null
  }
  void loadOverview()
}

onMounted(() => {
  void loadOverview()
})
</script>

<template>
  <div class="report-dashboard page-card">
    <div class="report-header">
      <div>
        <h2 class="report-title">报表分析</h2>
        <p class="report-desc">SLA 达成率、成本、异常与运力效率总览</p>
      </div>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        :clearable="true"
        :disabled="loading"
        @change="onDateRangeChange"
      />
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else-if="overview">
      <!-- ── KPI 卡片 ── -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon kpi-icon-blue"><span class="kpi-symbol">✓</span></div>
          <div class="kpi-body">
            <div class="kpi-value">
              {{ overview.sla.signed_orders }}
              <span class="kpi-unit">/ {{ overview.sla.total_orders }}</span>
            </div>
            <div class="kpi-label">已签收订单</div>
            <div class="kpi-tip">
              准时率
              <b :class="overview.sla.on_time_rate >= 0.6 ? 'ok' : 'bad'">
                {{ (overview.sla.on_time_rate * 100).toFixed(1) }}%
              </b>
            </div>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon kpi-icon-orange"><span class="kpi-symbol">¥</span></div>
          <div class="kpi-body">
            <div class="kpi-value">
              {{ overview.cost.total_cost.toFixed(0) }}
              <span class="kpi-unit">元</span>
            </div>
            <div class="kpi-label">运输成本</div>
            <div class="kpi-tip">
              {{ overview.cost.by_node.length }} 个节点产生路线成本
            </div>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon kpi-icon-red"><span class="kpi-symbol">!</span></div>
          <div class="kpi-body">
            <div class="kpi-value">{{ overview.exceptions.total_exceptions }}</div>
            <div class="kpi-label">异常事件</div>
            <div class="kpi-tip">
              未处理 <b class="bad">{{ overview.exceptions.open_count }}</b> ·
              已处理 {{ overview.exceptions.resolved_count }}
            </div>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon kpi-icon-green"><span class="kpi-symbol">🚚</span></div>
          <div class="kpi-body">
            <div class="kpi-value">
              {{ overview.capacity.delivering_count }}
              <span class="kpi-unit">/ {{ overview.capacity.total_vehicles }}</span>
            </div>
            <div class="kpi-label">在途车辆</div>
            <div class="kpi-tip">
              空闲 {{ overview.capacity.idle_count }} · 已送包裹
              {{ overview.capacity.delivered_package_count }}/{{
                overview.capacity.package_count
              }}
            </div>
          </div>
        </div>
      </div>

      <!-- ── SLA 仪表盘 + 异常饼图 ── -->
      <div class="chart-grid">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="chart-title">SLA 达成率</div>
          </template>
          <SlaGauge :sla="overview.sla" />
        </el-card>

        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="chart-title">异常类型分布</div>
          </template>
          <ExceptionPie :by-type="overview.exceptions.by_type" />
        </el-card>
      </div>

      <!-- ── 成本分布 ── -->
      <el-card shadow="never" class="chart-card chart-card-wide">
        <template #header>
          <div class="chart-title">成本分析</div>
        </template>
        <CostTrend :nodes="overview.cost.by_node" :vehicles="overview.cost.by_vehicle" />
      </el-card>

      <!-- ── 运力效率明细 ── -->
      <el-card shadow="never" class="chart-card chart-card-wide">
        <template #header>
          <div class="chart-title">运力效率明细</div>
        </template>
        <el-table
          :data="[
            {
              label: '在途车辆',
              value: `${overview.capacity.delivering_count} / ${overview.capacity.total_vehicles}`,
              note: 'delivering / 全部车辆',
            },
            {
              label: '空闲车辆',
              value: `${overview.capacity.idle_count}`,
              note: 'idle 状态',
            },
            {
              label: '调度明细',
              value: `${overview.capacity.dispatch_count}`,
              note: 'NodeDispatch 记录',
            },
            {
              label: '包裹送达率',
              value: `${(
                (overview.capacity.delivered_package_count /
                  Math.max(1, overview.capacity.package_count)) *
                100
              ).toFixed(1)}%`,
              note: `${overview.capacity.delivered_package_count} / ${overview.capacity.package_count}`,
            },
            {
              label: '平均行驶距离',
              value: `${overview.capacity.avg_distance_km} km`,
              note: '路线 total_distance 均值',
            },
          ]"
          :show-header="false"
          class="capacity-table"
        >
          <el-table-column prop="label" width="160">
            <template #default="{ row }">
              <span class="capacity-label">{{ row.label }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="value" width="200">
            <template #default="{ row }">
              <span class="capacity-value">{{ row.value }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="note" />
        </el-table>
      </el-card>
    </template>

    <el-empty v-else description="暂无报表数据，请稍后重试" />
  </div>
</template>

<style scoped>
.report-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.report-title {
  margin: 0 0 8px;
  font-size: 20px;
}

.report-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: var(--card-radius);
  border: 1px solid var(--meta-border, #ebeef5);
  background: #fff;
}

.kpi-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  flex: 0 0 auto;
}

.kpi-symbol {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}

.kpi-icon-blue {
  background-color: #409eff;
}
.kpi-icon-orange {
  background-color: #e6a23c;
}
.kpi-icon-red {
  background-color: #f56c6c;
}
.kpi-icon-green {
  background-color: #67c23a;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #303133);
  line-height: 1.2;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary, #909399);
}

.kpi-label {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-regular, #606266);
}

.kpi-tip {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.kpi-tip .ok {
  color: #67c23a;
}

.kpi-tip .bad {
  color: #f56c6c;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  border: 1px solid var(--meta-border, #ebeef5);
  margin-bottom: 16px;
}

.chart-card-wide {
  margin-bottom: 16px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.capacity-label {
  color: var(--text-regular, #606266);
}

.capacity-value {
  font-weight: 600;
  color: var(--text-primary, #303133);
}
</style>
