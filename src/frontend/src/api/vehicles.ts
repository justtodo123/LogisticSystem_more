import request from './request'
import type { ApiListParams, PaginatedResult } from '@/types/common'
import type { Vehicle, VehiclePayload } from '@/types/vehicle'
import { useMockBasicData } from '@/utils/env'
import { filterAndPaginate, nextCode } from '@/utils/mock'
import { getMockVehicles } from '@/utils/mock-store'

export async function listVehicles(
  params: ApiListParams = {},
): Promise<PaginatedResult<Vehicle>> {
  if (useMockBasicData()) {
    const vehicles = await getMockVehicles()
    return filterAndPaginate(vehicles, params, (item, p) => {
      if (p.node_code && item.node_code !== p.node_code) return false
      if (p.status && item.status !== p.status) return false
      return true
    })
  }
  const { data } = await request.get<PaginatedResult<Vehicle>>('/vehicles', {
    params,
  })
  return data
}

export async function createVehicle(payload: VehiclePayload): Promise<Vehicle> {
  if (useMockBasicData()) {
    const vehicles = await getMockVehicles()
    const item: Vehicle = {
      vehicle_type: 'normal',
      status: 'idle',
      ...payload,
      created_at: new Date().toISOString(),
    }
    vehicles.unshift(item)
    return item
  }
  const { data } = await request.post<Vehicle>('/vehicles', payload)
  return data
}

export async function updateVehicle(
  vehicleCode: string,
  payload: Partial<VehiclePayload>,
): Promise<Vehicle> {
  if (useMockBasicData()) {
    const vehicles = await getMockVehicles()
    const idx = vehicles.findIndex((v) => v.vehicle_code === vehicleCode)
    if (idx < 0) throw new Error('车辆不存在')
    vehicles[idx] = { ...vehicles[idx], ...payload }
    return vehicles[idx]
  }
  const { data } = await request.put<Vehicle>(
    `/vehicles/${vehicleCode}`,
    payload,
  )
  return data
}

export async function deleteVehicle(vehicleCode: string): Promise<void> {
  if (useMockBasicData()) {
    const vehicles = await getMockVehicles()
    const idx = vehicles.findIndex((v) => v.vehicle_code === vehicleCode)
    if (idx < 0) throw new Error('车辆不存在')
    if (vehicles[idx].status === 'delivering') {
      throw new Error('配送中的车辆不可删除')
    }
    vehicles.splice(idx, 1)
    return
  }
  await request.delete(`/vehicles/${vehicleCode}`)
}

export function suggestVehicleCode(existing: Vehicle[]): string {
  return nextCode('鄂A', existing.map((v) => v.vehicle_code))
}
