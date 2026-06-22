import type { ApiListParams } from '@/types/common'

export type ExceptionType = 'road' | 'node'

export type ExceptionStatus = 'open' | 'resolved'

export type RecommendedAction = 'redispatch' | 'reroute'

export type TargetType = 'node' | 'route' | 'vehicle'

export type ExceptionSubtype =
  | 'congestion'
  | 'damage'
  | 'capacity_limit'
  | 'road_closed'
  | 'road_accident'
  | 'storage_timeout'
  | 'node_maintenance'
  | 'vehicle_breakdown'

export interface ExceptionEvent {
  event_code: string
  exception_type: ExceptionType
  exception_subtype?: ExceptionSubtype | string | null
  target_type?: TargetType | null
  target_code?: string | null
  recommended_action: RecommendedAction
  related_schedule_code?: string | null
  replan_batch_code?: string | null
  description: string
  status: ExceptionStatus
  resolved_at?: string | null
  created_at?: string | null
}

export interface CreateExceptionPayload {
  exception_type: ExceptionType
  exception_subtype?: ExceptionSubtype | string
  target_type?: TargetType
  target_code?: string
  recommended_action: RecommendedAction
  related_schedule_code?: string
  description: string
}

export interface TriggerReplanPayload {
  action: RecommendedAction
  reason: string
}

export interface RedispatchReplanResult {
  schedule_code: string
  new_schedule_code: string
  batch_code: string
  version: number
  is_replan: boolean
  replan_reason: string
  original_schedule_code: string
}

export interface RerouteReplanResult {
  batch_code: string
  route_codes?: string[]
  new_route_code: string
  version: number
  is_replan: boolean
  replan_reason: string
  original_route_code: string
}

export type ReplanResult = RedispatchReplanResult | RerouteReplanResult

export interface ExceptionListParams extends ApiListParams {
  status?: ExceptionStatus | ''
  exception_type?: ExceptionType | ''
}
