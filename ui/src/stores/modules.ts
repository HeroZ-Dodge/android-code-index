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

  // 选中模块时只加载 overview + files，不预加载 deps（deps 按需懒加载）
  async function selectModuleFiles(module: string) {
    selectedModule.value = module
    const tasks: Promise<void>[] = []

    if (!overviewCache.value[module]) {
      tasks.push(
        getModuleOverview(module)
          .then((v: ModuleOverview) => { overviewCache.value[module] = v })
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

  // 懒加载 deps，仅在用户切换到依赖 Tab 时调用
  async function loadDeps(module: string) {
    if (depsCache.value[module] && 'sdk_deps' in depsCache.value[module]) return
    try {
      const v = await getModuleDeps(module)
      depsCache.value[module] = v
    } catch {}
  }

  // 兼容旧调用（onMounted 路由恢复时使用）
  async function selectModule(module: string) {
    return selectModuleFiles(module)
  }

  return {
    moduleList, selectedModule,
    overviewCache, depsCache, filesCache,
    loading, error,
    loadList, selectModule, selectModuleFiles, loadDeps,
  }
})
