/** 当前选中车辆路线 stroke 色（切换车辆时变化） */
export const ROUTE_STROKE_COLORS = [
  '#409eff',
  '#67c23a',
  '#e6a23c',
  '#f56c6c',
  '#909399',
  '#626aef',
  '#00bcd4',
  '#ff9800',
  '#9c27b0',
  '#795548',
] as const

export function routeColorForIndex(index: number): string {
  return ROUTE_STROKE_COLORS[index % ROUTE_STROKE_COLORS.length]
}
