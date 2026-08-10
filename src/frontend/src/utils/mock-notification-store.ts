import type {
  NotificationConfig,
  NotificationScenario,
  TestNotificationResult,
  UpdateNotificationConfigPayload,
} from '@/types/notification'

let config: NotificationConfig = {
  enabled_channels: ['console'],
  email_recipients: [],
  wechat_webhook_url: null,
  environment: 'mock',
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function getMockNotificationConfig(): Promise<NotificationConfig> {
  return { ...config, email_recipients: [...config.email_recipients] }
}

export async function updateMockNotificationConfig(
  payload: UpdateNotificationConfigPayload,
): Promise<NotificationConfig> {
  await delay(300)
  if (payload.enabled_channels !== undefined) {
    config.enabled_channels = payload.enabled_channels
  }
  if (payload.email_recipients !== undefined) {
    config.email_recipients = payload.email_recipients
  }
  if (payload.wechat_webhook_url !== undefined) {
    config.wechat_webhook_url = payload.wechat_webhook_url
  }
  return { ...config, email_recipients: [...config.email_recipients] }
}

export async function mockSendTestNotification(
  scenario: NotificationScenario,
): Promise<TestNotificationResult> {
  await delay(400)
  const results: Record<string, string> = {}
  for (const channel of config.enabled_channels) {
    if (channel === 'email' && config.email_recipients.length === 0) {
      results[channel] = 'failed'
    } else {
      results[channel] = 'ok'
    }
  }
  return { scenario, results }
}

export function resetMockNotificationStore(): void {
  config = {
    enabled_channels: ['console'],
    email_recipients: [],
    wechat_webhook_url: null,
    environment: 'mock',
  }
}
