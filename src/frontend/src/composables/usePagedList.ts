import { onMounted, ref } from 'vue'
import type { ApiListParams, PaginatedResult } from '@/types/common'

export function usePagedList<T>(
  fetchFn: (params: ApiListParams) => Promise<PaginatedResult<T>>,
  initialFilters: Record<string, string> = {},
) {
  const items = ref<T[]>([]) as { value: T[] }
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const filters = ref({ ...initialFilters })

  async function load(): Promise<void> {
    loading.value = true
    try {
      const result = await fetchFn({
        page: page.value,
        page_size: pageSize.value,
        ...filters.value,
      })
      items.value = result.items
      total.value = result.total
    } finally {
      loading.value = false
    }
  }

  function onPageChange(nextPage: number): void {
    page.value = nextPage
    load()
  }

  function onSizeChange(size: number): void {
    pageSize.value = size
    page.value = 1
    load()
  }

  function applyFilters(): void {
    page.value = 1
    load()
  }

  onMounted(() => {
    load()
  })

  return {
    items,
    total,
    page,
    pageSize,
    loading,
    filters,
    load,
    onPageChange,
    onSizeChange,
    applyFilters,
  }
}
