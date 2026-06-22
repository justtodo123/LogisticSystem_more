export interface GeoPoint {
  latitude: number
  longitude: number
}

export interface PixelPoint {
  x: number
  y: number
}

export interface GeoBounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

export interface SvgSize {
  width: number
  height: number
  padding?: number
}

export function computeBounds(points: GeoPoint[]): GeoBounds | null {
  if (!points.length) return null
  let minLat = points[0].latitude
  let maxLat = points[0].latitude
  let minLng = points[0].longitude
  let maxLng = points[0].longitude
  for (const p of points) {
    minLat = Math.min(minLat, p.latitude)
    maxLat = Math.max(maxLat, p.latitude)
    minLng = Math.min(minLng, p.longitude)
    maxLng = Math.max(maxLng, p.longitude)
  }
  return { minLat, maxLat, minLng, maxLng }
}

export function collectGeoPoints(data: {
  nodes: GeoPoint[]
  packages: GeoPoint[]
  segments: Array<{ start_lat: number; start_lng: number; end_lat: number; end_lng: number }>
}): GeoPoint[] {
  const points: GeoPoint[] = [
    ...data.nodes,
    ...data.packages,
    ...data.segments.flatMap((s) => [
      { latitude: s.start_lat, longitude: s.start_lng },
      { latitude: s.end_lat, longitude: s.end_lng },
    ]),
  ]
  return points
}

export function projectPoint(
  lat: number,
  lng: number,
  bounds: GeoBounds,
  size: SvgSize,
): PixelPoint {
  const padding = size.padding ?? 24
  const innerW = Math.max(size.width - padding * 2, 1)
  const innerH = Math.max(size.height - padding * 2, 1)
  const latSpan = bounds.maxLat - bounds.minLat || 0.01
  const lngSpan = bounds.maxLng - bounds.minLng || 0.01
  const x = padding + ((lng - bounds.minLng) / lngSpan) * innerW
  const y = padding + ((bounds.maxLat - lat) / latSpan) * innerH
  return { x, y }
}
