export interface PaginatedResult<T> {
  items: T[]
  total: number
  page?: number
  page_size?: number
}

export interface ApiListParams {
  page?: number
  page_size?: number
  [key: string]: string | number | undefined
}
