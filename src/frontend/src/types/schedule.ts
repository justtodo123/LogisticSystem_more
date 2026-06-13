export interface GlobalScheduleSummary {
  schedule_code: string
  total_distance: number
  total_time: number
  total_goods: number
  score: number
  package_count?: number
  version?: number
  is_replan?: boolean
  created_at?: string
}

export interface GoodsScheduleItem {
  goods_code: string
  order_code: string
  path: string[]
}

export interface GlobalScheduleDetail extends GlobalScheduleSummary {
  goods_schedules: GoodsScheduleItem[]
  order_codes?: string[]
  algorithm_type?: string
}

export interface GlobalScheduleCreatePayload {
  order_codes?: string[]
  algorithm?: string
  simulate_failure?: boolean
}
