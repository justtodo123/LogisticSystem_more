/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_USE_MOCK_AUTH: string
  readonly VITE_USE_MOCK_BASIC_DATA: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
