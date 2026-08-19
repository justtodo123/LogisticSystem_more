<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { GlobalScheduleSummary } from '@/types/schedule'
import { useAiParse } from '@/composables/useAiParse'
import { useAiExplain } from '@/composables/useAiExplain'
import {
  confirmAiSuggestion,
  rejectAiSuggestion,
} from '@/api/ai'
import type { AiSuggestionStatus } from '@/types/ai'
import EntityDetailDrawer from '@/components/detail/EntityDetailDrawer.vue'
import ExplainResultBody from '@/components/ai/ExplainResultBody.vue'

const props = defineProps<{
  schedules: GlobalScheduleSummary[]
  selectedScheduleCode?: string
}>()

const emit = defineEmits<{
  'draft-created': [scheduleCode: string]
}>()

const {
  message,
  targetMode,
  multiScheduleCodes,
  weightsEnabled,
  weights,
  loading,
  lastResult,
  lastMeta,
  canUseCurrentReplan,
  submit,
  tryP1,
  resetWeights,
} = useAiParse({
  selectedScheduleCode: () => props.selectedScheduleCode,
  scheduleCodes: () => props.schedules.map((s) => s.schedule_code),
  onDraftCreated: async (code) => {
    emit('draft-created', code)
  },
})

// ── T6-2 AI 建议确认闸门状态 ──
const suggestionDeciding = ref(false)
const decidedStatus = ref<AiSuggestionStatus | null>(null)

const currentSuggestionId = computed<number | null>(
  () => lastResult.value?.suggestion_id ?? null,
)
const currentSuggestionLevel = computed<string | null>(
  () => lastResult.value?.suggestion_level ?? null,
)

const suggestionLevelLabel = computed(() => {
  const level = currentSuggestionLevel.value
  if (level === 'suggestion') return '需调度员确认'
  if (level === 'action') return '自动执行'
  if (level === 'info') return '仅供参考'
  return null
})

const suggestionLevelTagType = computed(() => {
  const level = currentSuggestionLevel.value
  if (level === 'suggestion') return 'warning'
  if (level === 'action') return 'danger'
  return 'info'
})

const suggestionDecidedTag = computed(() => {
  const status = decidedStatus.value
  if (status === 'confirmed') return { type: 'success', text: '已确认应用' }
  if (status === 'rejected') return { type: 'info', text: '已拒绝' }
  return null
})

async function applySuggestion(): Promise<void> {
  const id = currentSuggestionId.value
  if (id == null || suggestionDeciding.value) return
  suggestionDeciding.value = true
  try {
    const result = await confirmAiSuggestion(id)
    decidedStatus.value = result.suggestion.status
    if (result.applied_schedule_code) {
      ElMessage.success(
        `AI 建议已确认，方案 ${result.applied_schedule_code} 已打包生效`,
      )
      emit('draft-created', result.applied_schedule_code)
    } else {
      ElMessage.success('AI 建议已确认')
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '确认失败')
  } finally {
    suggestionDeciding.value = false
  }
}

async function rejectSuggestionAction(): Promise<void> {
  const id = currentSuggestionId.value
  if (id == null || suggestionDeciding.value) return
  suggestionDeciding.value = true
  try {
    await rejectAiSuggestion(id)
    decidedStatus.value = 'rejected'
    ElMessage.info('AI 建议已拒绝')
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '拒绝失败')
  } finally {
    suggestionDeciding.value = false
  }
}

const {
  loading: explainLoading,
  drawerVisible: explainDrawerVisible,
  result: explainResult,
  meta: explainMeta,
  pendingMessage: explainPendingMessage,
  activeScheduleCode,
  explain,
  closeDrawer: closeExplainDrawer,
  clearPending: clearExplainPending,
} = useAiExplain()

const scheduleOptions = computed(() => props.schedules)

const explainDrawerTitle = computed(() => {
  const code = explainResult.value?.schedule_code ?? activeScheduleCode.value
  return code ? `AI 方案解释 · ${code}` : 'AI 方案解释'
})

const resultStatusLabel = computed(() => {
  if (!lastResult.value) return '—'
  if (lastResult.value.status === 'draft') return 'draft 预览'
  if (!lastResult.value.schedule_code) return 'dry-run'
  return '—'
})

function scheduleLabel(item: GlobalScheduleSummary): string {
  const parts = [item.schedule_code]
  if (item.version != null) parts.push(`v${item.version}`)
  if (item.is_replan) parts.push('重规划')
  return parts.join(' · ')
}

function onWeightChange(
  key: 'distance' | 'time' | 'package_count',
  value: number,
): void {
  const block = weights.global_schedule
  if (!block) return
  if (!block.weights) block.weights = {}
  block.weights[key] = value
}

function handleExplainClick(): void {
  explain(props.selectedScheduleCode)
}
</script>

<template>
  <el-card class="ai-panel" shadow="never">
    <template #header>
      <div class="ai-panel-header">
        <span>AI 智能助手（F014）</span>
        <el-tag size="small" type="info">自然语言调度</el-tag>
      </div>
    </template>

    <p class="ai-hint">
      描述调度偏好后发送，将生成 draft 预览方案；确认采用后才会打包落库。
      消息含「降级测试」可模拟 DeepSeek 降级。重规划方案 Mock 解释可演示降级提示。
    </p>

    <el-form label-position="top" class="ai-form">
      <el-form-item label="自然语言指令">
        <el-input
          v-model="message"
          type="textarea"
          :rows="3"
          placeholder="例如：优先缩短距离，多用电车"
          :disabled="loading"
        />
      </el-form-item>

      <el-form-item label="执行目标">
        <el-radio-group v-model="targetMode" :disabled="loading">
          <el-radio value="new">新建调度（全部待分配订单）</el-radio>
          <el-radio value="current" :disabled="!canUseCurrentReplan">
            重规划当前方案
          </el-radio>
          <el-radio value="multi">多选历史方案重规划</el-radio>
        </el-radio-group>
        <el-select
          v-if="targetMode === 'multi'"
          v-model="multiScheduleCodes"
          multiple
          filterable
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择方案"
          style="width: 100%; margin-top: 8px"
          :disabled="loading"
        >
          <el-option
            v-for="item in scheduleOptions"
            :key="item.schedule_code"
            :label="scheduleLabel(item)"
            :value="item.schedule_code"
          />
        </el-select>
        <p v-if="targetMode === 'multi'" class="multi-hint">
          后端 AI 接口仅对首个选中方案生成 draft 预览
        </p>
      </el-form-item>

      <el-collapse>
        <el-collapse-item title="手动权重（可选，P1-2 仅全局调度 F007 生效）" name="weights">
          <div class="weights-toolbar">
            <el-switch v-model="weightsEnabled" active-text="启用手动权重" />
            <el-button link type="primary" @click="resetWeights">恢复默认</el-button>
          </div>
          <template v-if="weightsEnabled">
            <p class="weights-section-title">全局调度 F007</p>
            <div class="weight-row">
              <span>距离</span>
              <el-slider
                :model-value="weights.global_schedule?.weights?.distance ?? 0.5"
                :min="0"
                :max="1"
                :step="0.05"
                :disabled="loading"
                @update:model-value="onWeightChange('distance', $event)"
              />
            </div>
            <div class="weight-row">
              <span>时效</span>
              <el-slider
                :model-value="weights.global_schedule?.weights?.time ?? 0.3"
                :min="0"
                :max="1"
                :step="0.05"
                :disabled="loading"
                @update:model-value="onWeightChange('time', $event)"
              />
            </div>
            <div class="weight-row">
              <span>包裹数</span>
              <el-slider
                :model-value="weights.global_schedule?.weights?.package_count ?? 0.2"
                :min="0"
                :max="1"
                :step="0.05"
                :disabled="loading"
                @update:model-value="onWeightChange('package_count', $event)"
              />
            </div>
          </template>
        </el-collapse-item>
      </el-collapse>

      <div class="ai-actions">
        <el-button
          type="primary"
          :loading="loading"
          :disabled="loading"
          @click="submit('draft')"
        >
          发送并生成预览
        </el-button>
        <el-button :loading="loading" :disabled="loading" @click="submit('dry-run')">
          仅预览参数
        </el-button>
      </div>
    </el-form>

    <el-alert
      v-if="lastMeta?.degraded"
      type="warning"
      :title="lastMeta.degraded_reason || 'DeepSeek 已降级'"
      show-icon
      :closable="false"
      class="ai-alert"
    />

    <div v-if="lastResult" class="ai-result">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="参数来源">
          {{ lastResult.mode }}
        </el-descriptions-item>
        <el-descriptions-item label="方案状态">
          {{ resultStatusLabel }}
        </el-descriptions-item>
        <el-descriptions-item v-if="lastResult.schedule_code" label="方案编号">
          {{ lastResult.schedule_code }}
        </el-descriptions-item>
        <el-descriptions-item v-if="lastResult.is_replan != null" label="重规划">
          {{ lastResult.is_replan ? '是' : '否' }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="lastResult.replan_results?.length" class="replan-list">
        <p class="result-subtitle">重规划结果</p>
        <el-table :data="lastResult.replan_results" size="small" border>
          <el-table-column prop="original_schedule_code" label="原方案" />
          <el-table-column prop="new_schedule_code" label="新方案" />
        </el-table>
      </div>

      <p class="result-subtitle">算法参数</p>
      <pre class="params-json">{{ JSON.stringify(lastResult.algorithm_params, null, 2) }}</pre>

      <div v-if="currentSuggestionId != null" class="suggestion-gate">
        <div class="suggestion-gate-header">
          <span class="result-subtitle">AI 建议确认闸门</span>
          <el-tag
            v-if="suggestionLevelLabel"
            :type="suggestionLevelTagType"
            size="small"
          >
            {{ currentSuggestionLevel }} · {{ suggestionLevelLabel }}
          </el-tag>
          <el-tag
            v-if="suggestionDecidedTag"
            :type="suggestionDecidedTag.type"
            size="small"
          >
            {{ suggestionDecidedTag.text }}
          </el-tag>
        </div>
        <p class="suggestion-gate-hint">
          确认后执行 F021 打包，draft 方案转为 active（实际调度生效）；拒绝仅记录，不触发调度修改。建议 ID：{{
            currentSuggestionId
          }}
        </p>
        <div
          v-if="!suggestionDecidedTag && currentSuggestionLevel !== 'info'"
          class="suggestion-gate-actions"
        >
          <el-button
            type="success"
            size="small"
            :loading="suggestionDeciding"
            :disabled="suggestionDeciding"
            @click="applySuggestion"
          >
            应用建议
          </el-button>
          <el-button
            size="small"
            :loading="suggestionDeciding"
            :disabled="suggestionDeciding"
            @click="rejectSuggestionAction"
          >
            拒绝
          </el-button>
        </div>
      </div>
    </div>

    <el-divider content-position="left">P1 功能</el-divider>

    <el-alert
      v-if="explainPendingMessage"
      type="info"
      :title="explainPendingMessage"
      show-icon
      :closable="true"
      class="ai-alert"
      @close="clearExplainPending"
    />

    <div class="p1-actions">
      <el-button
        size="small"
        :loading="explainLoading"
        :disabled="explainLoading"
        @click="handleExplainClick"
      >
        方案解释
      </el-button>
      <el-tooltip content="即将推出（P1）">
        <el-button
          size="small"
          @click="tryP1('review', selectedScheduleCode)"
        >
          方案审查
        </el-button>
      </el-tooltip>
      <el-tooltip content="即将推出（P1）">
        <el-button size="small" @click="tryP1('analyze')">
          异常分析
        </el-button>
      </el-tooltip>
    </div>

    <EntityDetailDrawer
      v-model="explainDrawerVisible"
      :title="explainDrawerTitle"
      :loading="explainLoading"
      @update:model-value="(v) => !v && closeExplainDrawer()"
    >
      <ExplainResultBody
        v-if="explainResult"
        :data="explainResult"
        :meta="explainMeta"
      />
    </EntityDetailDrawer>
  </el-card>
</template>

<style scoped>
.ai-panel {
  margin-top: 20px;
}

.ai-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ai-hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

.multi-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #909399;
}

.ai-form {
  margin-bottom: 8px;
}

.weights-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.weights-section-title {
  margin: 12px 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.weight-row {
  display: grid;
  grid-template-columns: 56px 1fr;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.ai-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.ai-alert {
  margin-top: 16px;
}

.ai-result {
  margin-top: 16px;
}

.result-subtitle {
  margin: 12px 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.params-json {
  margin: 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  overflow: auto;
  max-height: 240px;
}

.replan-list {
  margin-top: 12px;
}

.suggestion-gate {
  margin-top: 16px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}

.suggestion-gate-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.suggestion-gate-header .result-subtitle {
  margin: 0;
}

.suggestion-gate-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.suggestion-gate-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.p1-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
