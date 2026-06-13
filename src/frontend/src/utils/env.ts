export function useMockBasicData(): boolean {
  return import.meta.env.VITE_USE_MOCK_BASIC_DATA === 'true'
}
