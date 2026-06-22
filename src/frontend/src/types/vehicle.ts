export type VehicleStatus = 'idle' | 'delivering' | 'maintenance' | 'disabled'

export interface Vehicle {
  vehicle_code: string
  model: string
  capacity: number
  energy_type: string
  vehicle_type: string
  status: VehicleStatus
  node_code: string
  node_name?: string
  last_arrived_node_code: string
  last_arrived_node_name?: string
  created_at?: string
  updated_at?: string
}

export interface VehicleDetail extends Vehicle {
  node_name: string
  last_arrived_node_name: string
  capability_tags?: string[] | null
}

export interface VehiclePayload {
  vehicle_code: string
  model: string
  capacity: number
  energy_type: string
  vehicle_type?: string
  node_code: string
  last_arrived_node_code: string
  status?: VehicleStatus
}
