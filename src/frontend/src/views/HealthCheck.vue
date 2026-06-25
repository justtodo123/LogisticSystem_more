<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getHealth } from '@/api/health'

const loading = ref(false)
const result = ref('')
const error = ref('')

async function handleCheck() {
  loading.value = true
  result.value = ''
  error.value = ''

  try {
    const data = await getHealth()
    result.value = JSON.stringify(data, null, 2)
  } catch {
    error.value =
      '无法连接后端，请确认后端已在 8000 端口启动（见 docs/环境配置说明.md）'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-card health-check">
    <h2 class="health-title">后端联通测试</h2>
    <p class="health-desc">
      点击按钮请求 <code>GET /api/health</code>，验证 Vite 代理与后端服务是否正常。
    </p>
    <el-button type="primary" :loading="loading" @click="handleCheck">
      测试后端联通
    </el-button>

    <el-alert
      v-if="error"
      class="health-alert"
      type="error"
      :title="error"
      show-icon
      :closable="false"
    />

    <el-card v-if="result" class="health-result" shadow="never">
      <template #header>响应结果</template>
      <pre>{{ result }}</pre>
    </el-card>
  </div>
</template>

<style scoped>
.health-check {
  max-width: 640px;
}

.health-title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.health-desc {
  margin: 12px 0 20px;
  color: #606266;
}

.health-alert {
  margin-top: 20px;
}

.health-result {
  margin-top: 20px;
}

.health-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
