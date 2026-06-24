/** 路径节点（联调时后端可能返回此结构而非 path_labels） */
export interface PathNode {
  code: string
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
    const nameByCode = new Map(pathNodes.map((n) => [n.code, n.name]))
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
