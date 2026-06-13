import type { ApiListParams, PaginatedResult } from '@/types/common'

export function filterAndPaginate<T>(
  items: T[],
  params: ApiListParams,
  filterFn?: (item: T, params: ApiListParams) => boolean,
): PaginatedResult<T> {
  const page = Number(params.page ?? 1)
  const pageSize = Number(params.page_size ?? 20)
  const filtered = filterFn ? items.filter((item) => filterFn(item, params)) : items
  const start = (page - 1) * pageSize
  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
  }
}

export function nextCode(prefix: string, existing: string[]): string {
  const nums = existing
    .filter((c) => c.startsWith(prefix))
    .map((c) => parseInt(c.slice(prefix.length), 10))
    .filter((n) => !Number.isNaN(n))
  const next = nums.length > 0 ? Math.max(...nums) + 1 : 1
  return `${prefix}${String(next).padStart(3, '0')}`
}
