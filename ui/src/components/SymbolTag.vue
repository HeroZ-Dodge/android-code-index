<script setup lang="ts">
import type { SymbolKind } from '@/types'

defineProps<{ kind: SymbolKind | string }>()

const kindColors: Record<string, { bg: string; color: string }> = {
  class:               { bg: '#dbeafe', color: '#1d4ed8' },
  interface:           { bg: '#d1fae5', color: '#065f46' },
  object:              { bg: '#f3e8ff', color: '#6b21a8' },
  function:            { bg: '#fef3c7', color: '#92400e' },
  property:            { bg: '#ede9fe', color: '#5b21b6' },
  layout:              { bg: '#fce7f3', color: '#9d174d' },
  style:               { bg: '#fef9c3', color: '#713f12' },
  manifest_component:  { bg: '#fefce8', color: '#854d0e' },
  drawable:            { bg: '#ecfdf5', color: '#065f46' },
}

function getStyle(kind: string) {
  const c = kindColors[kind] ?? { bg: '#f3f4f6', color: '#374151' }
  return { background: c.bg, color: c.color }
}
</script>

<template>
  <span
    :style="getStyle(kind)"
    style="display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: 600; white-space: nowrap"
  >{{ kind }}</span>
</template>
