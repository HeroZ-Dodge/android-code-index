<script setup lang="ts">
import { androidColorToCss } from '@/utils/color'
defineProps<{ value: string | null | undefined }>()
</script>

<template>
  <span v-if="value" style="display: inline-flex; align-items: center; gap: 6px">
    <span
      :style="{ background: androidColorToCss(value) ?? 'transparent', border: '1px solid #d1d5db' }"
      style="display: inline-block; width: 16px; height: 16px; border-radius: 3px; flex-shrink: 0"
    />
    <span style="font-family: monospace; font-size: 12px">{{ value }}</span>
  </span>
  <span v-else style="color: #9ca3af">—</span>
</template>
