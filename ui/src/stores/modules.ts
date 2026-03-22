import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listModules, getModuleOverview, getModuleDeps, getModuleFiles } from '@/api/modules'
import type { ModuleListItem, ModuleOverview, ModuleDeps, ModuleFileGroup } from '@/types'

export const useModuleStore = defineStore('modules', () => {
  const moduleList = ref<ModuleListItem[]>([])
  const selectedModule = ref<string | null>(null)
  const overviewCache = ref<Record<string, ModuleOverview>>({})
  const depsCache = ref<Record<string, ModuleDeps>>({})
  const filesCache = ref<Record<string, ModuleFileGroup[]>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadList() {
    if (moduleList.value.length) return
    loading.value = true
    error.value = null
    try {
      moduleList.value = await listModules()
    } catch (e: any) {
      error.value = e?.message ?? '加载模块列表失败'
    } finally {
      loading.value = false
    }
  }

  async function selectModule(module: string) {
    selectedModule.value = module
    const tasks: Promise<void>[] = []

    if (!overviewCache.value[module]) {
      tasks.push(
        getModuleOverview(module)
          .then((v: ModuleOverview) => { overviewCache.value[module] = v })
          .catch(() => {})
      )
    }
    if (!depsCache.value[module]) {
      tasks.push(
        getModuleDeps(module)
          .then((v: ModuleDeps) => { depsCache.value[module] = v })
          .catch(() => {})
      )
    }
    if (!filesCache.value[module]) {
      tasks.push(
        getModuleFiles(module)
          .then((v: ModuleFileGroup[]) => { filesCache.value[module] = v })
          .catch(() => {})
      )
    }
    await Promise.all(tasks)
  }

  return {
    moduleList, selectedModule,
    overviewCache, depsCache, filesCache,
    loading, error,
    loadList, selectModule,
  }
})
