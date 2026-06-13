export function useMockBasicData(): boolean {
  return import.meta.env.VITE_USE_MOCK_BASIC_DATA === 'true'
}

export function useMockSchedule(): boolean {
  return import.meta.env.VITE_USE_MOCK_SCHEDULE === 'true'
}

export function useMockScheduleFail(): boolean {
  return import.meta.env.VITE_MOCK_SCHEDULE_FAIL === 'true'
}
