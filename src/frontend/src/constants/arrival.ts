import type { PackageArrivalExceptionSubtype } from '@/types/simulation'

export const ARRIVAL_DEMO_SCHEDULE = 'GS20260613001'
export const ARRIVAL_DEMO_NODE = 'SO101'

export const ARRIVAL_EXCEPTION_SUBTYPE_OPTIONS: {
  label: string
  value: PackageArrivalExceptionSubtype
}[] = [
  { label: '货损', value: 'damaged' },
  { label: '丢失', value: 'lost' },
  { label: '延误', value: 'delayed' },
  { label: '其他', value: 'other' },
]
