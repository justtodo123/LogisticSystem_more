/**
 * 高德地图 JS API v2.0 动态加载器（T5-2）
 *
 * - 全局单例：多次调用复用同一个 Promise
 * - 未配置 key 或加载失败时 reject，由调用方降级到 Canvas/SVG 渲染
 */

declare global {
  interface Window {
    AMap?: any
    _AMapSecurityConfig?: { securityJsCode?: string }
  }
}

let amapPromise: Promise<any> | null = null

export function loadAmap(key: string): Promise<any> {
  if (amapPromise) return amapPromise

  amapPromise = new Promise((resolve, reject) => {
    if (window.AMap) {
      resolve(window.AMap)
      return
    }

    const existing = document.querySelector<HTMLScriptElement>(
      'script[data-amap-loader]',
    )
    if (existing) {
      existing.addEventListener('load', () => resolve(window.AMap))
      existing.addEventListener('error', () =>
        reject(new Error('高德地图 JS API 加载失败')),
      )
      return
    }

    const script = document.createElement('script')
    script.dataset.amapLoader = '1'
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`
    script.async = true
    script.onload = () => {
      if (window.AMap) {
        resolve(window.AMap)
      } else {
        reject(new Error('高德地图 JS API 初始化异常'))
      }
    }
    script.onerror = () => reject(new Error('高德地图 JS API 脚本加载失败'))
    document.head.appendChild(script)
  })

  return amapPromise
}

export function isAmapConfigured(): boolean {
  return Boolean(import.meta.env.VITE_MAP_API_KEY)
}
