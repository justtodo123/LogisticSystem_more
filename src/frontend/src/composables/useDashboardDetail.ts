import { ref } from 'vue'
import { getGoods } from '@/api/goods'
import { getOrder } from '@/api/orders'
import { getPackage } from '@/api/packages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import type { NodeDispatchItem } from '@/types/dispatch'
import type { GoodsDetail } from '@/types/goods'
import type { OrderDetail } from '@/types/order'
import type { PackageDetail } from '@/types/package'

export function useDashboardDetail() {
  const goodsDetail = useEntityDetail<GoodsDetail>((code) => getGoods(code))
  const orderDetail = useEntityDetail<OrderDetail>((code) => getOrder(code))
  const packageDetail = useEntityDetail<PackageDetail>((code) =>
    getPackage(code),
  )

  const dispatchVisible = ref(false)
  const dispatchData = ref<NodeDispatchItem | null>(null)

  function openGoods(code: string): void {
    void goodsDetail.open(code, `货物 · ${code}`)
  }

  function openOrder(code: string): void {
    void orderDetail.open(code, `订单 · ${code}`)
  }

  function openPackage(code: string): void {
    void packageDetail.open(code, `包裹 · ${code}`)
  }

  function openDispatch(item: NodeDispatchItem): void {
    dispatchData.value = item
    dispatchVisible.value = true
  }

  function closeDispatch(): void {
    dispatchVisible.value = false
    dispatchData.value = null
  }

  return {
    goodsDetail,
    orderDetail,
    packageDetail,
    dispatchVisible,
    dispatchData,
    openGoods,
    openOrder,
    openPackage,
    openDispatch,
    closeDispatch,
  }
}
