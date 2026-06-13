export type NodeType = 'storage_center' | 'sorting_center'

export interface NodeItem {
  node_code: string
  name: string
  location: string
  latitude: number
  longitude: number
  node_type: NodeType
  capacity?: number
  inventory?: number
  level?: number
  max_storage_time?: number
  created_at?: string
}

export interface StorageCenterPayload {
  node_code: string
  name: string
  location: string
  latitude: number
  longitude: number
  capacity: number
  inventory?: number
}

export interface SortingCenterPayload {
  node_code: string
  name: string
  location: string
  latitude: number
  longitude: number
  level: number
  capacity?: number
  max_storage_time?: number
}
