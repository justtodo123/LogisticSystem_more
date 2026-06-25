export type AiParseMode = 'ai' | 'manual' | 'hybrid' | 'default'

export type AiExecuteMode = 'draft' | 'dry-run'

export interface AlgorithmWeights {
  distance?: number
  time?: number
  package_count?: number
}

export interface AlgorithmSectionConfig {
  algorithm?: string
  weights?: AlgorithmWeights
  max_iterations?: number
}

export interface AlgorithmParams {
  global_schedule?: AlgorithmSectionConfig
  node_dispatch?: AlgorithmSectionConfig
  route_planning?: AlgorithmSectionConfig
}

export interface AiParseRequest {
  message?: string
  weights?: AlgorithmParams
  schedule_codes?: string[]
  execute?: AiExecuteMode
}

export interface AiReplanResultItem {
  original_schedule_code: string
  new_schedule_code: string
}

export interface AiParseData {
  schedule_code?: string | null
  replan_results?: AiReplanResultItem[] | null
  algorithm_params: AlgorithmParams
  mode: AiParseMode
  is_replan?: boolean
  status?: 'draft'
  reference_codes?: string[] | null
}

export interface AiResponseMeta {
  degraded: boolean
  degraded_reason: string | null
}

export interface AiParseResult {
  data: AiParseData
  meta: AiResponseMeta
}

export type AiTargetMode = 'new' | 'current' | 'multi'

export interface AiExplainRequest {
  schedule_code: string
  detail_level?: 'brief' | 'detailed'
}

export interface AiReviewRequest {
  schedule_code: string
  check_items?: string[]
}

export interface AiAnalyzeExceptionRequest {
  exception_event_code: string
}
