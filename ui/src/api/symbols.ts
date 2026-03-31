import client from './client'
import type { Symbol } from '@/types'

export const getInheritance = (className: string): Promise<string[]> =>
  client.get(`/classes/${encodeURIComponent(className)}/inheritance`).then((r) => r.data)

export const getSubclasses = (className: string, directOnly = false, limit = 50): Promise<Symbol[]> =>
  client
    .get(`/classes/${encodeURIComponent(className)}/subclasses`, {
      params: { direct_only: directOnly, limit },
    })
    .then((r) => r.data)

export const getImplementations = (interfaceName: string, module?: string, limit = 50): Promise<Symbol[]> =>
  client
    .get(`/interfaces/${encodeURIComponent(interfaceName)}/implementations`, {
      params: { module, limit },
    })
    .then((r) => r.data)

// 精简版：只含摘要字段，不含 src_code
export const getClassApi = (className: string, includePrivate = false): Promise<Symbol[]> =>
  client
    .get(`/classes/${encodeURIComponent(className)}/api`, {
      params: { include_private: includePrivate },
    })
    .then((r) => r.data)

// 完整版：含 src_code 和 file_imports
export const getClassApiFull = (
  className: string,
  includePrivate = false,
): Promise<{ members: Symbol[]; file_imports: string[] }> =>
  client
    .get(`/classes/${encodeURIComponent(className)}/api/full`, {
      params: { include_private: includePrivate },
    })
    .then((r) => r.data)

// 按 id 获取单个符号的源码
export const getSymbolSource = (
  symbolId: number,
): Promise<{ id: number; name: string; kind: string; file_path: string; line_number: number | null; src_code: string }> =>
  client.get(`/symbols/${symbolId}/source`).then((r) => r.data)

export interface ClassInterfaces {
  all_interfaces: string[]
  per_class: { class: string; qualified_name: string; interfaces: string[] }[]
}

export const getClassInterfaces = (className: string): Promise<ClassInterfaces> =>
  client.get(`/classes/${encodeURIComponent(className)}/interfaces`).then((r) => r.data)

export const getFileSymbols = (filePath: string): Promise<Symbol[]> =>
  client.get(`/files/${filePath}/symbols`).then((r) => r.data)

export const getFileImports = (filePath: string): Promise<string[]> =>
  client.get(`/files/${encodeURIComponent(filePath)}/imports`).then((r) => r.data)
