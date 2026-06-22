import request from './request'
import type {
  SimulationDeliverPayload,
  SimulationDeliverResult,
} from '@/types/simulation'
import { useMockSimulation } from '@/utils/env'
import { simulateDeliverMock } from '@/utils/mock-simulation'

function compactPayload(
  payload: SimulationDeliverPayload,
): SimulationDeliverPayload {
  const body: SimulationDeliverPayload = {}
  if (payload.batch_code) body.batch_code = payload.batch_code
  if (payload.vehicle_code) body.vehicle_code = payload.vehicle_code
  if (payload.package_code) body.package_code = payload.package_code
  return body
}

export async function simulateDeliver(
  payload: SimulationDeliverPayload = {},
): Promise<SimulationDeliverResult> {
  if (useMockSimulation()) {
    return simulateDeliverMock(payload)
  }
  const { data } = await request.post<SimulationDeliverResult>(
    '/simulation/deliver',
    compactPayload(payload),
  )
  return data
}
