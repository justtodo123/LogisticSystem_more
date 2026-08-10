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
  /** T6-2：AI 建议确认闸门 — parse 成功后返回的建议记录与级别 */
  suggestion_id?: number | null
  suggestion_level?: AiSuggestionLevel | null
}

export type AiSuggestionLevel = 'info' | 'suggestion' | 'action'

export type AiSuggestionStatus = 'pending' | 'confirmed' | 'rejected'

export interface AiSuggestion {
  id: number
  suggestion_code: string
  level: AiSuggestionLevel
  source: string
  title: string
  content: string
  payload?: AlgorithmParams | null
  related_schedule_code?: string | null
  status: AiSuggestionStatus
  applied_schedule_code?: string | null
  decision_note?: string | null
  created_at?: string | null
  decided_at?: string | null
}

export interface AiSuggestionList {
  items: AiSuggestion[]
  total: number
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

export interface AiExplainSections {
  reasoning?: string
  key_decisions?: string[]
  risks?: string[]
  suggestions?: string[]
}

/** 后端 POST /ai/explain 原始响应 data 字段 */
export interface AiExplainRawData {
  explanation: string
  key_decisions?: string[]
  potential_risks?: string[]
  suggestions?: string[]
}

export interface AiExplainData {
  schedule_code: string
  explanation: string
  sections?: AiExplainSections
}

export interface AiExplainResult {
  data: AiExplainData | null
  meta: AiResponseMeta
  pending?: boolean
  message?: string
}

export interface AiReviewRequest {
  schedule_code: string
  check_items?: string[]
}

export interface AiAnalyzeExceptionRequest {
  exception_event_code: string
}
