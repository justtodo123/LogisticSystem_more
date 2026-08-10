export type NotificationChannelName = 'console' | 'email' | 'wechat_work'

export type NotificationScenario =
  | 'schedule_confirmed'
  | 'exception_created'
  | 'replan_completed'
  | 'arrival_confirmed'

export interface NotificationConfig {
  enabled_channels: NotificationChannelName[]
  email_recipients: string[]
  wechat_webhook_url: string | null
  environment: string
}

export interface UpdateNotificationConfigPayload {
  enabled_channels?: NotificationChannelName[]
  email_recipients?: string[]
  wechat_webhook_url?: string | null
}

export interface TestNotificationResult {
  scenario: NotificationScenario
  results: Record<string, string>
}

export const NOTIFICATION_SCENARIO_LABELS: Record<NotificationScenario, string> = {
  schedule_confirmed: '调度方案确认',
  exception_created: '异常发生',
  replan_completed: '重规划完成',
  arrival_confirmed: '送达确认',
}
