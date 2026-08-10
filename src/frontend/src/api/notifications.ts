import request from './request'
import type {
  NotificationConfig,
  NotificationScenario,
  TestNotificationResult,
  UpdateNotificationConfigPayload,
} from '@/types/notification'
import { useMockNotifications } from '@/utils/env'
import {
  getMockNotificationConfig,
  mockSendTestNotification,
  updateMockNotificationConfig,
} from '@/utils/mock-notification-store'

export async function getNotificationConfig(): Promise<NotificationConfig> {
  if (useMockNotifications()) {
    return getMockNotificationConfig()
  }

  const { data } = await request.get<NotificationConfig>('/notifications/config')
  return data
}

export async function updateNotificationConfig(
  payload: UpdateNotificationConfigPayload,
): Promise<NotificationConfig> {
  if (useMockNotifications()) {
    return updateMockNotificationConfig(payload)
  }

  const { data } = await request.put<NotificationConfig>(
    '/notifications/config',
    payload,
  )
  return data
}

export async function sendTestNotification(
  scenario: NotificationScenario,
): Promise<TestNotificationResult> {
  if (useMockNotifications()) {
    return mockSendTestNotification(scenario)
  }

  const { data } = await request.post<TestNotificationResult>(
    '/notifications/test',
    { scenario },
  )
  return data
}
