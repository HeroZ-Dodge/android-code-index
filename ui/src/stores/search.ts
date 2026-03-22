import { defineStore } from 'pinia'
import { ref } from 'vue'
import { search as apiSearch } from '@/api/search'
import type { Symbol } from '@/types'

export const useSearchStore = defineStore('search', () => {
  const keyword = ref('')
  const kindFilter = ref<string | null>(null)
  const moduleFilter = ref<string | null>(null)
  const results = ref<Symbol[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref<20 | 50 | 100>(20)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function doSearch() {
    if (!keyword.value.trim()) return
    loading.value = true
    error.value = null
    try {
      const res = await apiSearch({
        keyword: keyword.value,
        kind: kindFilter.value || undefined,
        module: moduleFilter.value || undefined,
        limit: pageSize.value,
        offset: (page.value - 1) * pageSize.value,
      })
      results.value = res.items
      total.value = res.total
    } catch (e: any) {
      error.value = e?.message ?? '搜索失败'
    } finally {
      loading.value = false
    }
  }

  function resetPage() {
    page.value = 1
  }

  return {
    keyword, kindFilter, moduleFilter,
    results, total, page, pageSize,
    loading, error,
    doSearch, resetPage,
  }
})
