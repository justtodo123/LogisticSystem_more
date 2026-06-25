import type { NodeDispatchItem } from '@/types/dispatch'
import type { RouteCoordinates, RouteSegment } from '@/types/route'
import { buildRouteOverlayFromSegments, computeCargoRouteMetrics } from '@/utils/route-normalize'

/** 武汉演示区域节点坐标（与 init_demo_data 量级一致） */
const NODE_COORDS: Record<string, { lat: number; lng: number }> = {
  SC001: { lat: 30.5, lng: 114.4 },
  SC002: { lat: 30.4, lng: 114.3 },
  SC003: { lat: 30.45, lng: 114.35 },
  SC004: { lat: 30.48, lng: 114.42 },
  SC005: { lat: 30.42, lng: 114.38 },
  L1001: { lat: 30.52, lng: 114.35 },
  L1002: { lat: 30.46, lng: 114.32 },
}

function resolveNodeCoord(nodeCode: string): { lat: number; lng: number } {
  if (NODE_COORDS[nodeCode]) {
    return NODE_COORDS[nodeCode]
  }
  const prefix = nodeCode.slice(0, 2)
  if (prefix === 'SC') return { lat: 30.48, lng: 114.36 }
  if (prefix === 'L1') return { lat: 30.5, lng: 114.34 }
  if (prefix === 'L2') return { lat: 30.47, lng: 114.33 }
  let hash = 0
  for (let i = 0; i < nodeCode.length; i++) {
    hash = (hash + nodeCode.charCodeAt(i) * (i + 1)) % 997
  }
  return {
    lat: 30.44 + (hash % 20) * 0.005,
    lng: 114.28 + (hash % 25) * 0.004,
  }
}

/** 从节点间调度明细动态生成 Mock 路线坐标 */
export function buildMockRouteCoordinates(
  vehicleCode: string,
  dispatch: NodeDispatchItem,
): RouteCoordinates {
  const segments: RouteSegment[] = []

  const tasks = dispatch.tasks.filter((t) => !t.is_return)

  for (const task of tasks) {
    const from = resolveNodeCoord(task.from_node_code)
    const to = resolveNodeCoord(task.to_node_code)

    segments.push({
      road_name: '虚拟路段',
      start_lng: from.lng,
      start_lat: from.lat,
      end_lng: to.lng,
      end_lat: to.lat,
    })
  }

  const overlay = buildRouteOverlayFromSegments(segments, dispatch)
  const metrics = computeCargoRouteMetrics(segments)

  return {
    vehicle_code: vehicleCode,
    route_code: `RT-MOCK-${dispatch.dispatch_code}`,
    nodes: overlay.nodes,
    packages: overlay.packages,
    segments,
    total_distance: metrics.distance,
    total_time: metrics.time,
  }
}

/** RouteMap 开发用静态样例 */
export function sampleRouteCoordinates(): RouteCoordinates {
  return buildMockRouteCoordinates('VEHSC00101', {
    dispatch_code: 'DISP-SAMPLE',
    vehicle_code: 'VEHSC00101',
    driver_code: 'DRVSC00101',
    level_phase: 0,
    total_distance: 12.5,
    tasks: [
      {
        from_node_code: 'SC001',
        to_node_code: 'L1001',
        package_codes: ['PKG001', 'PKG002'],
      },
    ],
  })
}
