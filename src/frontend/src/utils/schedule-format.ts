/** 路径节点（联调时后端返回此结构） */
export interface PathNode {
  node_code: string
  node_name?: string
  /** @deprecated Mock 旧格式兼容 */
  code?: string
  name?: string
}

export function formatPathWithLabels(
  path: string[],
  pathLabels?: string[],
): string {
  if (!path.length) return '—'
  return path
    .map((code, i) => {
      const label = pathLabels?.[i]
      return label && label !== code ? `${code}(${label})` : code
    })
    .join(' → ')
}

/** 联调适配：path + path_labels 或 path_nodes */
export function resolvePathLabels(
  path: string[],
  pathLabels?: string[],
  pathNodes?: PathNode[],
): string[] | undefined {
  if (pathLabels?.length) return pathLabels
  if (pathNodes?.length) {
    const nameByCode = new Map(
      pathNodes.map((n) => [n.node_code ?? n.code ?? '', n.node_name ?? n.name]),
    )
    return path.map((code) => nameByCode.get(code) ?? code)
  }
  return undefined
}

export function formatNodeWithName(
  code?: string | null,
  name?: string,
): string {
  if (!code) return '—'
  return name && name !== code ? `${code}(${name})` : code
}
