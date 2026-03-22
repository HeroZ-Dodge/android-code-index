import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getInheritance, getSubclasses, getImplementations, getClassApi } from '@/api/symbols'
import type { Symbol } from '@/types'

export const useDrawerStore = defineStore('drawer', () => {
  const visible = ref(false)
  const symbol = ref<Symbol | null>(null)
  const inheritanceChain = ref<string[]>([])
  const subclasses = ref<Symbol[]>([])
  const implementations = ref<Symbol[]>([])
  const members = ref<Symbol[]>([])
  const loading = ref(false)

  async function open(s: Symbol) {
    symbol.value = s
    visible.value = true
    inheritanceChain.value = []
    subclasses.value = []
    implementations.value = []
    members.value = []
    loading.value = true

    const tasks: Promise<void>[] = []

    if (s.kind === 'class' || s.kind === 'object') {
      tasks.push(
        getInheritance(s.name).then((v: string[]) => { inheritanceChain.value = v }).catch(() => {})
      )
      tasks.push(
        getSubclasses(s.name).then((v: Symbol[]) => { subclasses.value = v }).catch(() => {})
      )
      tasks.push(
        getClassApi(s.name).then((v: Symbol[]) => { members.value = v }).catch(() => {})
      )
    } else if (s.kind === 'interface') {
      tasks.push(
        getImplementations(s.name).then((v: Symbol[]) => { implementations.value = v }).catch(() => {})
      )
    }

    await Promise.all(tasks)
    loading.value = false
  }

  function close() {
    visible.value = false
    symbol.value = null
  }

  return {
    visible, symbol,
    inheritanceChain, subclasses, implementations, members,
    loading,
    open, close,
  }
})
