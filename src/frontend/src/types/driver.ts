export type DriverStatus = 'idle' | 'busy'

export interface Driver {
  driver_code: string
  name: string
  phone: string
  license_type: string
  shift: string
  node_code: string
  node_name?: string
  status: DriverStatus
  created_at?: string
  updated_at?: string
}

export interface DriverDetail extends Driver {
  node_name: string
}
