import client from './client'
import type { ModuleListItem, ModuleOverview, ModuleDeps, ModuleFileGroup } from '@/types'

export const listModules = (): Promise<ModuleListItem[]> =>
  client.get('/modules').then((r) => r.data)

export const getModuleOverview = (module: string): Promise<ModuleOverview> =>
  client.get(`/modules/${encodeURIComponent(module)}/overview`).then((r) => r.data)

export const getModuleDeps = (module: string): Promise<ModuleDeps> =>
  client.get(`/modules/${encodeURIComponent(module)}/dependencies`).then((r) => r.data)

export const getModuleFiles = (module: string, sourceSet?: string): Promise<ModuleFileGroup[]> =>
  client
    .get(`/modules/${encodeURIComponent(module)}/files`, {
      params: sourceSet ? { source_set: sourceSet } : undefined,
    })
    .then((r) => r.data)
