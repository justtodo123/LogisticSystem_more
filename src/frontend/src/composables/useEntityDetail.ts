import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useEntityDetail<T>(fetcher: (code: string) => Promise<T>) {
  const visible = ref(false)
  const loading = ref(false)
  const data = ref<T | null>(null)
  const title = ref('详情')

  async function open(code: string, drawerTitle?: string): Promise<void> {
    visible.value = true
    loading.value = true
    data.value = null
    title.value = drawerTitle ?? `详情 · ${code}`
    try {
      data.value = await fetcher(code)
    } catch (err) {
      ElMessage.error(err instanceof Error ? err.message : '加载详情失败')
      visible.value = false
    } finally {
      loading.value = false
    }
  }

  function close(): void {
    visible.value = false
    data.value = null
  }

  return { visible, loading, data, title, open, close }
}
