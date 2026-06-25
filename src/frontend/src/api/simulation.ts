import request from './request'
import type {
  ConfirmArrivalPayload,
  ConfirmArrivalResult,
  GetArrivalPackagesParams,
  GetArrivalPackagesResult,
  SimulationDeliverPayload,
  SimulationDeliverResponse,
  SimulationDeliverResult,
} from '@/types/simulation'
import { useMockSimulation } from '@/utils/env'
import {
  confirmArrivalMock,
  getArrivalPackagesMock,
} from '@/utils/mock-arrival-store'
import { simulateDeliverMock } from '@/utils/mock-simulation'

function compactPayload(
  payload: SimulationDeliverPayload,
): Omit<SimulationDeliverPayload, 'batch_code'> {
  const body: Omit<SimulationDeliverPayload, 'batch_code'> = {}
  if (payload.vehicle_code) body.vehicle_code = payload.vehicle_code
  if (payload.package_code) body.package_code = payload.package_code
  return body
}

function toResult(data: SimulationDeliverResponse): SimulationDeliverResult {
  const count = data.delivered_package_codes.length
  return {
    packages_delivered: count,
    delivered_package_codes: data.delivered_package_codes,
    message:
      count > 0
        ? `已模拟送达 ${count} 个包裹`
        : '未送达包裹',
  }
}

export async function simulateDeliver(
  payload: SimulationDeliverPayload = {},
): Promise<SimulationDeliverResult> {
  if (useMockSimulation()) {
    return simulateDeliverMock(payload)
  }
  const { data } = await request.post<SimulationDeliverResponse>(
    '/simulation/deliver',
    compactPayload(payload),
  )
  return toResult(data)
}

export async function getArrivalPackages(
  params: GetArrivalPackagesParams,
): Promise<GetArrivalPackagesResult> {
  if (useMockSimulation()) {
    return getArrivalPackagesMock(params)
  }
  const { data } = await request.get<GetArrivalPackagesResult>(
    '/simulation/arrival-packages',
    { params },
  )
  return data
}

export async function confirmArrival(
  payload: ConfirmArrivalPayload,
): Promise<ConfirmArrivalResult> {
  if (useMockSimulation()) {
    return confirmArrivalMock(payload)
  }
  const { data } = await request.post<ConfirmArrivalResult>(
    '/simulation/confirm-arrival',
    payload,
  )
  return data
}
