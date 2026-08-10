import type { PackageGoodsItem } from '@/types/package'

export type ScheduleStatus = 'draft' | 'active' | 'discarded'

export interface ScoreBreakdown {
  distance_component: number
  time_component: number
  goods_component: number
  formula?: string
}

/** T2-3 分项评分（多目标） */
export interface ScoreBreakdownItem {
  objective: string
  metric?: string
  raw?: number | null
  weight: number
  direction: 'minimize' | 'maximize'
  score?: number | null
}

export interface ConstraintHit {
  name: string
  detail: string
  severity: 'info' | 'warning'
  hit: boolean
}

/** T2-3 结构化解释：评分拆解 + 约束命中 + 备选方案 */
export interface ScheduleExplanation {
  score_breakdown?: ScoreBreakdownItem[]
  composite_score?: number | null
  constraints_hit?: ConstraintHit[]
  alternatives?: Array<{
    profile: string
    overall_score: number
    total_distance: number
    total_time: number
  }>
  summary?: string
}

export interface GlobalScheduleSummary {
  schedule_code: string
  total_distance: number
  total_time: number
  total_goods: number
  score: number
  score_display?: number
  score_breakdown?: ScoreBreakdown
  explanation?: ScheduleExplanation
  package_count?: number
  version?: number
  is_replan?: boolean
  status?: ScheduleStatus
  created_at?: string
}

export interface GoodsScheduleItem {
  goods_code: string
  order_code: string
  path: string[]
  goods_name?: string
  path_labels?: string[]
}

export interface SchedulePackageItem {
  package_code: string
  weight: number
  volume: number
  status: string
  from_node_code?: string | null
  to_node_code?: string | null
  from_node_name?: string
  to_node_name?: string
  goods_items?: PackageGoodsItem[]
}

export interface GlobalScheduleDetail extends GlobalScheduleSummary {
  goods_schedules: GoodsScheduleItem[]
  packages?: SchedulePackageItem[]
  order_codes?: string[]
  algorithm_type?: string
}

export interface GlobalScheduleCreatePayload {
  order_codes?: string[]
  algorithm: string
  preview?: boolean
  simulate_failure?: boolean
}

export interface DiscardDraftResult {
  schedule_code: string
  status: 'discarded'
}
