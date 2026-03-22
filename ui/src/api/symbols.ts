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

export const getClassApi = (className: string, includePrivate = false): Promise<Symbol[]> =>
  client
    .get(`/classes/${encodeURIComponent(className)}/api`, {
      params: { include_private: includePrivate },
    })
    .then((r) => r.data)

export const getFileSymbols = (filePath: string): Promise<Symbol[]> =>
  client.get(`/files/${filePath}/symbols`).then((r) => r.data)
