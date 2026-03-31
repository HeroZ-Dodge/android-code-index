import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getInheritance, getSubclasses, getImplementations, getClassApi, getSymbolSource, getClassInterfaces } from '@/api/symbols'
import type { Symbol } from '@/types'
import type { ClassInterfaces } from '@/api/symbols'

export const useDrawerStore = defineStore('drawer', () => {
  const visible = ref(false)
  const symbol = ref<Symbol | null>(null)
  const inheritanceChain = ref<string[]>([])
  const subclasses = ref<Symbol[]>([])
  const implementations = ref<Symbol[]>([])
  const members = ref<Symbol[]>([])
  const classInterfaces = ref<ClassInterfaces | null>(null)
  const loading = ref(false)

  // 按需加载的成员源码缓存：member.id -> src_code
  const memberSrcCache = ref<Record<number, string | null>>({})
  const memberSrcLoading = ref<Set<number>>(new Set())

  async function open(s: Symbol) {
    symbol.value = s
    visible.value = true
    inheritanceChain.value = []
    subclasses.value = []
    implementations.value = []
    members.value = []
    classInterfaces.value = null
    memberSrcCache.value = {}
    memberSrcLoading.value = new Set()
    loading.value = true

    const tasks: Promise<void>[] = []

    if (s.kind === 'class' || s.kind === 'object') {
      tasks.push(
        getClassInterfaces(s.qualified_name).then((v) => { classInterfaces.value = v }).catch(() => {})
      )
      tasks.push(
        getInheritance(s.qualified_name).then((v) => { inheritanceChain.value = v }).catch(() => {})
      )
      tasks.push(
        getSubclasses(s.qualified_name).then((v) => { subclasses.value = v }).catch(() => {})
      )
      tasks.push(
        // 精简版：快速加载成员摘要，传 qualified_name 避免同名歧义
        getClassApi(s.qualified_name).then((v) => { members.value = v }).catch(() => {})
      )
    } else if (s.kind === 'interface') {
      tasks.push(
        getImplementations(s.qualified_name).then((v) => { implementations.value = v }).catch(() => {})
      )
    }

    await Promise.all(tasks)
    loading.value = false
  }

  // 按需加载单个成员的源码
  async function loadMemberSource(memberId: number) {
    if (memberId in memberSrcCache.value) return
    if (memberSrcLoading.value.has(memberId)) return

    memberSrcLoading.value = new Set([...memberSrcLoading.value, memberId])
    try {
      const result = await getSymbolSource(memberId)
      memberSrcCache.value = { ...memberSrcCache.value, [memberId]: result.src_code }
    } catch {
      memberSrcCache.value = { ...memberSrcCache.value, [memberId]: null }
    } finally {
      const next = new Set(memberSrcLoading.value)
      next.delete(memberId)
      memberSrcLoading.value = next
    }
  }

  function close() {
    visible.value = false
    symbol.value = null
  }

  return {
    visible, symbol,
    inheritanceChain, subclasses, implementations, members, classInterfaces,
    memberSrcCache, memberSrcLoading,
    loading,
    open, close, loadMemberSource,
  }
})
