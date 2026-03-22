import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStats, getStatsBreakdown } from '@/api/stats'
import { listModules } from '@/api/modules'
import type { ProjectStats, StatsBreakdown, ModuleListItem } from '@/types'

export const useStatsStore = defineStore('stats', () => {
  const stats = ref<ProjectStats | null>(null)
  const breakdown = ref<StatsBreakdown | null>(null)
  const moduleList = ref<ModuleListItem[]>([])
  const loadedAt = ref<number | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load(force = false) {
    if (!force && loadedAt.value && Date.now() - loadedAt.value < 60000) return
    loading.value = true
    error.value = null
    try {
      const [s, b, m] = await Promise.all([getStats(), getStatsBreakdown(), listModules()])
      stats.value = s
      breakdown.value = b
      moduleList.value = m
      loadedAt.value = Date.now()
    } catch (e: any) {
      error.value = e?.message ?? '加载失败'
    } finally {
      loading.value = false
    }
  }

  return { stats, breakdown, moduleList, loadedAt, loading, error, load }
})
