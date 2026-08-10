<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageToolbar from '@/components/crud/PageToolbar.vue'
import {
  getNotificationConfig,
  sendTestNotification,
  updateNotificationConfig,
} from '@/api/notifications'
import { NOTIFICATION_SCENARIO_LABELS } from '@/types/notification'
import type {
  NotificationChannelName,
  NotificationConfig,
  NotificationScenario,
} from '@/types/notification'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const environment = ref('')

const CHANNEL_OPTIONS: Array<{ label: string; value: NotificationChannelName; desc: string }> = [
  { label: '控制台 (Console)', value: 'console', desc: '开发环境，print 输出' },
  { label: '邮件 (Email)', value: 'email', desc: 'SMTP 发送，需配置收件人' },
  { label: '企业微信 (WeChat Work)', value: 'wechat_work', desc: '群机器人 Webhook' },
]

const form = reactive({
  enabled_channels: [] as NotificationChannelName[],
  email_recipients: '',
  wechat_webhook_url: '',
})

async function load(): Promise<void> {
  loading.value = true
  try {
    const cfg: NotificationConfig = await getNotificationConfig()
    environment.value = cfg.environment
    form.enabled_channels = [...cfg.enabled_channels]
    form.email_recipients = cfg.email_recipients.join(', ')
    form.wechat_webhook_url = cfg.wechat_webhook_url ?? ''
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载通知配置失败')
  } finally {
    loading.value = false
  }
}

async function save(): Promise<void> {
  if (form.enabled_channels.length === 0) {
    ElMessage.warning('请至少选择一个通知渠道')
    return
  }
  saving.value = true
  try {
    const recipients = form.email_recipients
      .split(',')
      .map((r) => r.trim())
      .filter(Boolean)
    await updateNotificationConfig({
      enabled_channels: form.enabled_channels,
      email_recipients: recipients,
      wechat_webhook_url: form.wechat_webhook_url.trim() || null,
    })
    ElMessage.success('通知渠道配置已更新（运行时生效）')
    await load()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function test(scenario: NotificationScenario): Promise<void> {
  testing.value = true
  try {
    const result = await sendTestNotification(scenario)
    const summary = Object.entries(result.results)
      .map(([ch, status]) => `${ch}=${status === 'ok' ? '成功' : '失败'}`)
      .join('；')
    ElMessage.info(`【${NOTIFICATION_SCENARIO_LABELS[scenario]}】${summary || '未启用任何渠道'}`)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '测试通知失败')
  } finally {
    testing.value = false
  }
}

const scenarioEntries = Object.entries(NOTIFICATION_SCENARIO_LABELS) as Array<
  [NotificationScenario, string]
>

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="page-card">
    <PageToolbar title="消息通知设置" :description="`运行环境：${environment || '—'}`" />

    <el-card v-loading="loading" class="notify-card" shadow="never">
      <template #header>
        <span>通知渠道</span>
      </template>

      <el-form label-width="120px">
        <el-form-item label="启用渠道">
          <el-checkbox-group v-model="form.enabled_channels">
            <el-checkbox
              v-for="opt in CHANNEL_OPTIONS"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
              <span class="channel-desc">{{ opt.desc }}</span>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item
          v-if="form.enabled_channels.includes('email')"
          label="邮件收件人"
        >
          <el-input
            v-model="form.email_recipients"
            placeholder="逗号分隔，如 ops@example.com, ops2@example.com"
          />
        </el-form-item>

        <el-form-item
          v-if="form.enabled_channels.includes('wechat_work')"
          label="企业微信 Webhook"
        >
          <el-input
            v-model="form.wechat_webhook_url"
            placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
          <el-button @click="load">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="notify-card" shadow="never">
      <template #header>
        <span>发送测试</span>
      </template>
      <p class="test-hint">
        向当前启用的渠道发送一条测试通知，验证渠道可用性。
      </p>
      <div class="test-buttons">
        <el-button
          v-for="[scenario, label] in scenarioEntries"
          :key="scenario"
          :loading="testing"
          @click="test(scenario)"
        >
          测试：{{ label }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.notify-card {
  margin-top: 16px;
}

.channel-desc {
  margin-left: 6px;
  color: #909399;
  font-size: 12px;
}

.test-hint {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}

.test-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
