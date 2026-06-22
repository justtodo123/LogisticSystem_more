export function useMockBasicData(): boolean {
  return import.meta.env.VITE_USE_MOCK_BASIC_DATA === 'true'
}

export function useMockSchedule(): boolean {
  return import.meta.env.VITE_USE_MOCK_SCHEDULE === 'true'
}

export function useMockScheduleFail(): boolean {
  return import.meta.env.VITE_MOCK_SCHEDULE_FAIL === 'true'
}

export function useMockNodeDispatch(): boolean {
  return import.meta.env.VITE_USE_MOCK_NODE_DISPATCH === 'true'
}

export function useMockRoutes(): boolean {
  return import.meta.env.VITE_USE_MOCK_ROUTES === 'true'
}

export function useMockSimulation(): boolean {
  return import.meta.env.VITE_USE_MOCK_SIMULATION === 'true'
}

export function useMockExceptions(): boolean {
  return import.meta.env.VITE_USE_MOCK_EXCEPTIONS === 'true'
}

export function useMockAi(): boolean {
  return import.meta.env.VITE_USE_MOCK_AI === 'true'
}
