import type { DispatchTask, NodeDispatchItem } from '@/types/dispatch'
import type {
  BackendRouteCoordinate,
  BackendRouteCoordinatesResponse,
  RouteDetailResponse,
  RouteCoordinates,
  RouteNodePoint,
  RoutePackagePoint,
  RouteSegment,
} from '@/types/route'

/** 武汉演示区域节点坐标（与 init_demo_data / mock-route-builder 一致） */
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

/** 从 dispatch tasks 推导节点与包裹坐标（后端 coordinates 接口不返回） */
export function buildRouteOverlayFromDispatch(
  dispatch: NodeDispatchItem,
): { nodes: RouteNodePoint[]; packages: RoutePackagePoint[] } {
  const nodeMap = new Map<string, RouteNodePoint>()
  const packages: RoutePackagePoint[] = []

  for (const task of dispatch.tasks.filter((t) => !t.is_return)) {
    const from = resolveNodeCoord(task.from_node_code)
    const to = resolveNodeCoord(task.to_node_code)

    if (!nodeMap.has(task.from_node_code)) {
      nodeMap.set(task.from_node_code, {
        node_code: task.from_node_code,
        latitude: from.lat,
        longitude: from.lng,
        role: task.from_node_code.startsWith('SC') ? 'depot' : 'hub',
      })
    }
    if (!nodeMap.has(task.to_node_code)) {
      nodeMap.set(task.to_node_code, {
        node_code: task.to_node_code,
        latitude: to.lat,
        longitude: to.lng,
        role: task.to_node_code.startsWith('L2') ? 'destination' : 'hub',
      })
    }

    for (const pkg of task.package_codes) {
      packages.push({
        package_code: pkg,
        latitude: to.lat + 0.002,
        longitude: to.lng + 0.002,
      })
    }
  }

  return { nodes: [...nodeMap.values()], packages }
}

function nodeRole(nodeCode: string): string | undefined {
  if (nodeCode.startsWith('SC')) return 'depot'
  if (nodeCode.startsWith('L2')) return 'destination'
  if (nodeCode.startsWith('L1') || nodeCode.startsWith('SO')) return 'hub'
  return undefined
}

function upsertNode(
  nodeMap: Map<string, RouteNodePoint>,
  nodeCode: string,
  lat: number,
  lng: number,
): void {
  const existing = nodeMap.get(nodeCode)
  if (existing) {
    existing.latitude = lat
    existing.longitude = lng
    return
  }
  nodeMap.set(nodeCode, {
    node_code: nodeCode,
    latitude: lat,
    longitude: lng,
    role: nodeRole(nodeCode),
  })
}

function haversineKm(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const toRad = (d: number) => (d * Math.PI) / 180
  const R = 6371
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

/** segment 与 dispatch.tasks 同索引；仅保留带货 task 对应的段 */
export function cargoSegmentTaskPairs(
  segments: RouteSegment[],
  dispatch?: NodeDispatchItem | null,
): Array<{ seg: RouteSegment; task: DispatchTask | undefined }> {
  const tasks = dispatch?.tasks
  if (!tasks?.length) {
    return segments.map((seg) => ({ seg, task: undefined }))
  }
  return segments
    .map((seg, index) => ({ seg, task: tasks[index] }))
    .filter(({ task }) => !task?.is_return)
}

export function filterCargoSegments(
  segments: RouteSegment[],
  dispatch?: NodeDispatchItem | null,
): RouteSegment[] {
  return cargoSegmentTaskPairs(segments, dispatch).map((p) => p.seg)
}

export function computeCargoRouteMetrics(cargoSegments: RouteSegment[]): {
  distance: number
  time: number
} {
  let distance = 0
  for (const seg of cargoSegments) {
    distance += haversineKm(
      seg.start_lat,
      seg.start_lng,
      seg.end_lat,
      seg.end_lng,
    )
  }
  distance = Math.round(distance * 10) / 10
  const time = Math.round((distance / 60) * 60)
  return { distance, time }
}

/** 从 route_segments 与 dispatch tasks 推导节点/包裹，坐标与折线端点对齐（仅带货段） */
export function buildRouteOverlayFromSegments(
  segments: RouteSegment[],
  dispatch?: NodeDispatchItem | null,
): { nodes: RouteNodePoint[]; packages: RoutePackagePoint[] } {
  const nodeMap = new Map<string, RouteNodePoint>()
  const packages: RoutePackagePoint[] = []

  cargoSegmentTaskPairs(segments, dispatch).forEach(({ seg, task }, index) => {
    const fromCode = task?.from_node_code ?? `N${index}S`
    const toCode = task?.to_node_code ?? `N${index}E`

    upsertNode(nodeMap, fromCode, seg.start_lat, seg.start_lng)
    upsertNode(nodeMap, toCode, seg.end_lat, seg.end_lng)

    if (task?.package_codes?.length) {
      for (const pkg of task.package_codes) {
        packages.push({
          package_code: pkg,
          latitude: seg.end_lat + 0.002,
          longitude: seg.end_lng + 0.002,
        })
      }
    }
  })

  return { nodes: [...nodeMap.values()], packages }
}

function buildRouteOverlay(
  segments: RouteSegment[],
  dispatch?: NodeDispatchItem | null,
): { nodes: RouteNodePoint[]; packages: RoutePackagePoint[] } {
  if (segments.length > 0) {
    return buildRouteOverlayFromSegments(segments, dispatch)
  }
  if (dispatch?.tasks?.length) {
    return buildRouteOverlayFromDispatch(dispatch)
  }
  return { nodes: [], packages: [] }
}

export function segmentsFromRouteDetail(
  routeSegments: RouteDetailResponse['route_segments'],
): RouteSegment[] {
  return routeSegments.map((seg) => ({
    road_name: seg.road_name,
    start_lng: seg.start_lng,
    start_lat: seg.start_lat,
    end_lng: seg.end_lng,
    end_lat: seg.end_lat,
  }))
}

export function segmentsFromPolyline(
  coordinates: BackendRouteCoordinate['coordinates'],
): RouteSegment[] {
  const segments: RouteSegment[] = []
  for (let i = 0; i < coordinates.length - 1; i++) {
    const [startLng, startLat] = coordinates[i]
    const [endLng, endLat] = coordinates[i + 1]
    segments.push({
      road_name: '虚拟道路',
      start_lng: startLng,
      start_lat: startLat,
      end_lng: endLng,
      end_lat: endLat,
    })
  }
  return segments
}

export function pickRouteForBatch(
  data: BackendRouteCoordinatesResponse,
  batchCode?: string,
): BackendRouteCoordinate | null {
  if (!data.routes.length) return null
  if (batchCode) {
    const matched = data.routes.find((r) => r.batch_code === batchCode)
    if (matched) return matched
  }
  return data.routes[0]
}

function normalizeRouteData(
  vehicleCode: string,
  routeCode: string,
  allSegments: RouteSegment[],
  dispatch?: NodeDispatchItem | null,
): RouteCoordinates {
  const cargoSegments = filterCargoSegments(allSegments, dispatch)
  const overlay = buildRouteOverlay(allSegments, dispatch)
  const metrics = computeCargoRouteMetrics(cargoSegments)

  return {
    vehicle_code: vehicleCode,
    route_code: routeCode,
    nodes: overlay.nodes,
    packages: overlay.packages,
    segments: cargoSegments,
    total_distance: metrics.distance,
    total_time: metrics.time,
  }
}

export function normalizeFromRouteDetail(
  vehicleCode: string,
  detail: RouteDetailResponse,
  dispatch?: NodeDispatchItem | null,
): RouteCoordinates {
  const allSegments =
    detail.route_segments?.length > 0
      ? segmentsFromRouteDetail(detail.route_segments)
      : []

  return normalizeRouteData(
    vehicleCode,
    detail.route_code,
    allSegments,
    dispatch,
  )
}

export function normalizeRouteCoordinates(
  vehicleCode: string,
  coordData: BackendRouteCoordinatesResponse,
  detail: RouteDetailResponse,
  dispatch?: NodeDispatchItem | null,
): RouteCoordinates {
  const route = pickRouteForBatch(coordData, detail.batch_code ?? undefined)
  if (!route) {
    throw new Error('该车辆暂无路线，请先完成路径规划')
  }

  const allSegments =
    detail.route_segments?.length > 0
      ? segmentsFromRouteDetail(detail.route_segments)
      : segmentsFromPolyline(route.coordinates)

  return normalizeRouteData(
    vehicleCode,
    route.route_code,
    allSegments,
    dispatch,
  )
}
