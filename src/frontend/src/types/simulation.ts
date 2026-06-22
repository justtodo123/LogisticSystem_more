import type { BatchStatus } from '@/types/dispatch'

export interface SimulationDeliverPayload {
  batch_code?: string
  vehicle_code?: string
  package_code?: string
}

export interface SimulationDeliverResult {
  packages_delivered: number
  batch_status?: BatchStatus
  message?: string
}
