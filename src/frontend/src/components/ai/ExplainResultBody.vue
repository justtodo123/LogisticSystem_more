<script setup lang="ts">
import type { AiExplainData, AiResponseMeta } from '@/types/ai'

defineProps<{
  data: AiExplainData
  meta?: AiResponseMeta | null
}>()
</script>

<template>
  <div class="explain-body">
    <el-alert
      v-if="meta?.degraded"
      type="warning"
      :title="meta.degraded_reason || 'DeepSeek 已降级，以下为模板解释'"
      show-icon
      :closable="false"
      class="explain-alert"
    />

    <section class="explain-section">
      <h3 class="explain-section-title">解释摘要</h3>
      <p class="explain-text">{{ data.explanation }}</p>
    </section>

    <section v-if="data.sections?.key_decisions?.length" class="explain-section">
      <h3 class="explain-section-title">关键决策</h3>
      <ul class="explain-list">
        <li v-for="(item, index) in data.sections.key_decisions" :key="`decision-${index}`">
          <el-tag type="info" size="small" effect="plain">{{ item }}</el-tag>
        </li>
      </ul>
    </section>

    <section v-if="data.sections?.reasoning" class="explain-section">
      <h3 class="explain-section-title">调度原因</h3>
      <p class="explain-text">{{ data.sections.reasoning }}</p>
    </section>

    <section v-if="data.sections?.risks?.length" class="explain-section">
      <h3 class="explain-section-title">潜在风险</h3>
      <ul class="explain-list">
        <li v-for="(item, index) in data.sections.risks" :key="`risk-${index}`">
          <el-tag type="warning" size="small" effect="plain">{{ item }}</el-tag>
        </li>
      </ul>
    </section>

    <section v-if="data.sections?.suggestions?.length" class="explain-section">
      <h3 class="explain-section-title">优化建议</h3>
      <ul class="explain-list">
        <li v-for="(item, index) in data.sections.suggestions" :key="`suggest-${index}`">
          <el-tag type="success" size="small" effect="plain">{{ item }}</el-tag>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.explain-body {
  display: flex;
  flex-direction: column;
  gap: var(--section-gap, 12px);
}

.explain-alert {
  margin-bottom: 4px;
}

.explain-section-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.explain-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-regular, #606266);
  white-space: pre-wrap;
}

.explain-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
