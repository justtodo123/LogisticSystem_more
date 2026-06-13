import type { Driver } from '@/types/driver'
import type { Goods } from '@/types/goods'
import type { NodeItem } from '@/types/node'
import type { PackageItem } from '@/types/package'
import type { Order } from '@/types/order'
import type { Vehicle } from '@/types/vehicle'

let nodesData: NodeItem[] | null = null
let ordersData: Order[] | null = null
let vehiclesData: Vehicle[] | null = null
let goodsData: Goods[] | null = null
let packagesData: PackageItem[] | null = null
let driversData: Driver[] | null = null

async function loadJson<T>(path: string): Promise<T[]> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`加载 Mock 数据失败: ${path}`)
  return res.json() as Promise<T[]>
}

export async function getMockNodes(): Promise<NodeItem[]> {
  if (!nodesData) {
    nodesData = await loadJson<NodeItem>('/mock/nodes.json')
  }
  return nodesData
}

export async function getMockOrders(): Promise<Order[]> {
  if (!ordersData) {
    ordersData = await loadJson<Order>('/mock/orders.json')
  }
  return ordersData
}

export async function getMockVehicles(): Promise<Vehicle[]> {
  if (!vehiclesData) {
    vehiclesData = await loadJson<Vehicle>('/mock/vehicles.json')
  }
  return vehiclesData
}

export async function getMockGoods(): Promise<Goods[]> {
  if (!goodsData) {
    goodsData = await loadJson<Goods>('/mock/goods.json')
  }
  return goodsData
}

export async function getMockPackages(): Promise<PackageItem[]> {
  if (!packagesData) {
    packagesData = await loadJson<PackageItem>('/mock/packages.json')
  }
  return packagesData
}

export async function getMockDrivers(): Promise<Driver[]> {
  if (!driversData) {
    driversData = await loadJson<Driver>('/mock/drivers.json')
  }
  return driversData
}

export function resetMockStore(): void {
  nodesData = null
  ordersData = null
  vehiclesData = null
  goodsData = null
  packagesData = null
  driversData = null
}
