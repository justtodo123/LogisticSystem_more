import type { DriverStatus } from '@/types/driver'
import type { GoodsStatus } from '@/types/goods'
import type { PackageStatus } from '@/types/package'
import type { OrderStatus } from '@/types/order'
import type { VehicleStatus } from '@/types/vehicle'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

export const ORDER_STATUS_MAP: Record<
  OrderStatus,
  { label: string; tag: TagType }
> = {
  pending: { label: '待分配', tag: 'info' },
  delivering: { label: '配送中', tag: 'primary' },
  completed: { label: '已完成', tag: 'success' },
  exception: { label: '异常', tag: 'danger' },
}

export const ORDER_STATUS_OPTIONS = Object.entries(ORDER_STATUS_MAP).map(
  ([value, { label }]) => ({ value, label }),
)

export const VEHICLE_STATUS_MAP: Record<
  VehicleStatus,
  { label: string; tag: TagType }
> = {
  idle: { label: '空闲', tag: 'success' },
  delivering: { label: '配送中', tag: 'primary' },
  maintenance: { label: '维护中', tag: 'warning' },
  disabled: { label: '停用', tag: 'info' },
}

export const VEHICLE_STATUS_OPTIONS = Object.entries(VEHICLE_STATUS_MAP).map(
  ([value, { label }]) => ({ value, label }),
)

export const ENERGY_TYPE_OPTIONS = [
  { value: 'electric', label: '电动' },
  { value: 'fuel', label: '燃油' },
  { value: 'hybrid', label: '混动' },
]

export const GOODS_STATUS_MAP: Record<
  GoodsStatus,
  { label: string; tag: TagType }
> = {
  pending_pack: { label: '待打包', tag: 'info' },
  packed: { label: '已打包', tag: 'primary' },
  in_transit: { label: '运输中', tag: 'warning' },
  delivered: { label: '已送达', tag: 'success' },
  exception: { label: '异常', tag: 'danger' },
}

export const GOODS_STATUS_OPTIONS = Object.entries(GOODS_STATUS_MAP).map(
  ([value, { label }]) => ({ value, label }),
)

export const PACKAGE_STATUS_MAP: Record<
  PackageStatus,
  { label: string; tag: TagType }
> = {
  pending_pack: { label: '待打包', tag: 'info' },
  packed: { label: '已打包', tag: 'primary' },
  in_transit: { label: '运输中', tag: 'warning' },
  delivered: { label: '已送达', tag: 'success' },
  exception: { label: '异常', tag: 'danger' },
}

export const PACKAGE_STATUS_OPTIONS = Object.entries(PACKAGE_STATUS_MAP).map(
  ([value, { label }]) => ({ value, label }),
)

export const DRIVER_STATUS_MAP: Record<
  DriverStatus,
  { label: string; tag: TagType }
> = {
  idle: { label: '空闲', tag: 'success' },
  busy: { label: '忙碌', tag: 'primary' },
}

export const DRIVER_STATUS_OPTIONS = Object.entries(DRIVER_STATUS_MAP).map(
  ([value, { label }]) => ({ value, label }),
)
