/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_USE_MOCK_AUTH: string
  readonly VITE_USE_MOCK_BASIC_DATA: string
  readonly VITE_USE_MOCK_SCHEDULE: string
  readonly VITE_MOCK_SCHEDULE_FAIL?: string
  readonly VITE_USE_MOCK_NODE_DISPATCH: string
  readonly VITE_USE_MOCK_ROUTES: string
  readonly VITE_USE_MOCK_SIMULATION: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
