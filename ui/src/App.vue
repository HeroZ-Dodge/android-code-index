<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import SymbolDrawer from '@/components/SymbolDrawer.vue'

const route = useRoute()
const networkError = ref(false)

function onNetworkError() {
  networkError.value = true
}

onMounted(() => {
  window.addEventListener('api:network-error', onNetworkError)
})
onUnmounted(() => {
  window.removeEventListener('api:network-error', onNetworkError)
})

const navLinks = [
  { path: '/', label: '仪表板' },
  { path: '/search/code', label: '源码搜索' },
  { path: '/search/resource', label: '资源搜索' },
  { path: '/modules', label: '模块浏览' },
  { path: '/relationships', label: '关系图谱' },
  { path: '/resources', label: '资源浏览' },
  { path: '/playground', label: 'API Playground' },
]
</script>

<template>
  <el-container direction="vertical" style="min-height: 100vh">
    <!-- 网络不可达 Banner -->
    <el-alert
      v-if="networkError"
      title="无法连接到索引服务，请确认后端已启动（python main.py serve http）"
      type="error"
      :closable="true"
      @close="networkError = false"
      show-icon
      style="border-radius: 0"
    />

    <!-- 顶部导航 -->
    <el-header height="56px" style="background: #1a1a2e; padding: 0 24px; display: flex; align-items: center; gap: 24px; flex-shrink: 0">
      <span style="color: #fff; font-weight: 700; font-size: 16px; margin-right: 8px">
        Android Code Index
      </span>
      <router-link
        v-for="link in navLinks"
        :key="link.path"
        :to="link.path"
        style="text-decoration: none"
      >
        <el-button
          :type="route.path === link.path || (link.path !== '/' && route.path.startsWith(link.path)) ? 'primary' : 'text'"
          size="small"
          :style="{ color: route.path === link.path || (link.path !== '/' && route.path.startsWith(link.path)) ? undefined : '#a8b4d0' }"
        >
          {{ link.label }}
        </el-button>
      </router-link>
    </el-header>

    <!-- 页面内容 -->
    <el-main style="padding: 24px; background: #f5f7fa">
      <router-view />
    </el-main>

    <!-- 全局符号详情抽屉 -->
    <SymbolDrawer />
  </el-container>
</template>

<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
a { color: inherit; }
</style>
