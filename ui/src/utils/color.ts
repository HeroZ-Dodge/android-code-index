/**
 * Android 颜色格式 → CSS 颜色
 * 支持 #RGB, #RRGGBB, #ARGB, #AARRGGBB
 */
export function androidColorToCss(color: string | null | undefined): string | null {
  if (!color) return null
  const hex = color.replace('#', '')

  if (hex.length === 3) {
    // #RGB
    return `#${hex}`
  }
  if (hex.length === 6) {
    // #RRGGBB
    return `#${hex}`
  }
  if (hex.length === 4) {
    // #ARGB → rgba
    const a = parseInt(hex[0] + hex[0], 16) / 255
    const r = parseInt(hex[1] + hex[1], 16)
    const g = parseInt(hex[2] + hex[2], 16)
    const b = parseInt(hex[3] + hex[3], 16)
    return `rgba(${r},${g},${b},${a.toFixed(2)})`
  }
  if (hex.length === 8) {
    // #AARRGGBB → rgba
    const a = parseInt(hex.slice(0, 2), 16) / 255
    const r = parseInt(hex.slice(2, 4), 16)
    const g = parseInt(hex.slice(4, 6), 16)
    const b = parseInt(hex.slice(6, 8), 16)
    return `rgba(${r},${g},${b},${a.toFixed(2)})`
  }
  return color
}
