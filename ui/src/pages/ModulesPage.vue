<script setup lang="ts">
import { ref, computed, onMounted, shallowReactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useModuleStore } from '@/stores/modules'
import { useDrawerStore } from '@/stores/drawer'
import { getFileSymbols } from '@/api/symbols'
import SymbolTag from '@/components/SymbolTag.vue'
import type { Symbol, ModuleFile } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useModuleStore()
const drawer = useDrawerStore()

onMounted(async () => {
  await store.loadList()
  const name = route.params.name as string | undefined
  if (name && !store.selectedModule) {
    await store.selectModule(decodeURIComponent(name))
  }
})

const filterText = ref('')
const filteredModules = computed(() =>
  filterText.value
    ? store.moduleList.filter((m: { module: string }) => m.module.includes(filterText.value))
    : store.moduleList
)

async function selectMod(mod: string) {
  // 切换模块时清空展开状态（用新对象替换，单次响应式更新）
  Object.keys(expandedFiles).forEach(k => delete expandedFiles[k])
  Object.keys(fileError).forEach(k => delete fileError[k])
  Object.keys(loadingFiles).forEach(k => delete loadingFiles[k])
  Object.keys(collapsedDirs).forEach(k => delete collapsedDirs[k])
  depsTabActivated.value = false
  activeTab.value = 'files'
  await store.selectModuleFiles(mod)
  router.replace({ path: `/modules/${encodeURIComponent(mod)}` })
}

// 文件树状态
const expandedFiles = shallowReactive<Record<string, Symbol[]>>({})
const loadingFiles = shallowReactive<Record<string, boolean>>({})
const fileError = shallowReactive<Record<string, string>>({})
const collapsedDirs = shallowReactive<Record<string, boolean>>({})

function isDirCollapsed(dirPath: string): boolean {
  return collapsedDirs[dirPath] !== false
}

function toggleDir(dirPath: string) {
  collapsedDirs[dirPath] = isDirCollapsed(dirPath) ? false : true
}

async function toggleFile(file: ModuleFile) {
  const key = file.file_path
  if (expandedFiles[key]) {
    delete expandedFiles[key]
    delete fileError[key]
    return
  }
  loadingFiles[key] = true
  delete fileError[key]
  try {
    const encodedPath = encodeURIComponent(file.file_path.replace(/^\//, ''))
    const symbols = await getFileSymbols(encodedPath)
    expandedFiles[key] = symbols
    if (symbols.length === 0) {
      fileError[key] = '该文件无符号'
    }
  } catch (e: any) {
    fileError[key] = e?.message ?? '加载符号失败'
    console.error('加载文件符号失败:', file.file_path, e)
  } finally {
    delete loadingFiles[key]
  }
}

const activeTab = ref('files')
// 依赖 Tab 是否已激活过（懒加载：首次切过去才请求）
const depsTabActivated = ref(false)

async function onTabChange(tab: string) {
  activeTab.value = tab
  if (tab === 'deps' && !depsTabActivated.value && store.selectedModule) {
    depsTabActivated.value = true
    await store.loadDeps(store.selectedModule)
  }
}

const overview = computed(() =>
  store.selectedModule ? store.overviewCache[store.selectedModule] : null
)
const deps = computed(() =>
  store.selectedModule ? store.depsCache[store.selectedModule] : null
)
const files = computed(() =>
  store.selectedModule ? store.filesCache[store.selectedModule] : null
)

const statsCards = computed(() => [
  { label: '文件数', value: overview.value?.files },
  { label: 'SDK 类', value: overview.value?.sdk_classes },
  { label: 'impl 类', value: overview.value?.impl_classes },
  { label: '接口', value: overview.value?.interfaces },
  { label: '函数', value: overview.value?.functions },
])
</script>

<template>
  <div style="display: flex; gap: 20px; align-items: flex-start; min-height: 600px">
    <!-- 左侧模块列表 -->
    <div style="width: 240px; flex-shrink: 0">
      <el-card shadow="never" style="height: 100%">
        <template #header>
          <div style="display: flex; align-items: center; justify-content: space-between">
            <span>模块列表</span>
            <el-tag size="small" type="info">{{ store.moduleList.length }}</el-tag>
          </div>
        </template>
        <el-input v-model="filterText" placeholder="过滤模块" size="small" clearable style="margin-bottom: 12px" />
        <el-alert v-if="store.error" :title="store.error" type="error" :closable="false" size="small" />
        <el-skeleton :loading="store.loading" animated :rows="5">
          <template #default>
            <div style="max-height: calc(100vh - 200px); overflow-y: auto">
              <div
                v-for="m in filteredModules"
                :key="m.module"
                @click="selectMod(m.module)"
                :style="{
                  background: store.selectedModule === m.module ? '#eef2ff' : '',
                  border: store.selectedModule === m.module ? '1px solid #c7d2fe' : '1px solid transparent',
                }"
                style="padding: 10px 12px; border-radius: 8px; cursor: pointer; margin-bottom: 4px; transition: background 0.15s, border-color 0.15s"
              >
                <div style="font-weight: 600; font-size: 13px; color: #2d3561; word-break: break-all">{{ m.module }}</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 2px">
                  {{ m.symbol_count }} 符号 · {{ m.file_count }} 文件
                </div>
              </div>
            </div>
          </template>
        </el-skeleton>
      </el-card>
    </div>

    <!-- 右侧详情 -->
    <div style="flex: 1; min-width: 0">
      <div v-if="!store.selectedModule" style="display: flex; align-items: center; justify-content: center; height: 300px; color: #9ca3af">
        点击左侧模块查看详情
      </div>

      <template v-else>
        <!-- 统计卡片 -->
        <el-row :gutter="12" style="margin-bottom: 16px">
          <el-col :span="4" v-for="card in statsCards" :key="card.label">
            <el-card shadow="never" body-style="padding: 12px; text-align: center">
              <div style="font-size: 22px; font-weight: 700; color: #2d3561">{{ card.value ?? '—' }}</div>
              <div style="font-size: 12px; color: #6b7280">{{ card.label }}</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Tab 区域 -->
        <el-card shadow="never">
          <el-tabs v-model="activeTab" @tab-change="onTabChange">
            <!-- 文件树 Tab -->
            <el-tab-pane label="文件树" name="files">
              <div v-if="!files" style="color: #9ca3af; text-align: center; padding: 24px">加载中...</div>
              <div v-else-if="!files.length" style="color: #9ca3af; text-align: center; padding: 24px">无文件</div>
              <template v-else>
                <div v-for="group in files" :key="group.dir_path" style="margin-bottom: 4px">
                  <!-- 目录行：可点击折叠/展开 -->
                  <div
                    @click="toggleDir(group.dir_path)"
                    style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; font-family: monospace; padding: 4px 8px; background: #f8f9fc; border-radius: 4px; cursor: pointer; user-select: none"
                    class="dir-row"
                  >
                    <el-icon style="font-size: 11px; flex-shrink: 0; transition: transform 0.15s" :style="{ transform: isDirCollapsed(group.dir_path) ? 'rotate(-90deg)' : 'rotate(0deg)' }">
                      <component is="ArrowDown" />
                    </el-icon>
                    <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ group.dir_path }}</span>
                    <el-tag size="small" type="info" style="flex-shrink: 0">{{ group.files.length }}</el-tag>
                  </div>

                  <!-- 目录内文件列表：折叠时不渲染，避免大量 DOM -->
                  <template v-if="!isDirCollapsed(group.dir_path)">
                    <div
                      v-for="file in group.files"
                      :key="file.file_path"
                      style="margin-left: 16px; margin-top: 4px"
                    >
                      <div
                        @click="toggleFile(file)"
                        style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 6px; cursor: pointer; background: #fff; border: 1px solid #e5e7eb"
                      >
                        <el-icon :style="{ color: loadingFiles[file.file_path] ? '#9ca3af' : '#6b7280' }">
                          <component :is="expandedFiles[file.file_path] ? 'FolderOpened' : loadingFiles[file.file_path] ? 'Loading' : 'Document'" />
                        </el-icon>
                        <span style="font-family: monospace; font-size: 12px; flex: 1">
                          {{ file.file_path.split('/').pop() }}
                        </span>
                        <el-tag size="small" type="info">{{ file.file_type }}</el-tag>
                        <el-tag size="small">{{ file.symbol_count }}</el-tag>
                      </div>

                      <!-- 加载状态 -->
                      <div v-if="loadingFiles[file.file_path]" style="margin-left: 24px; margin-top: 4px; color: #9ca3af; font-size: 12px">
                        加载中...
                      </div>

                      <!-- 错误提示 -->
                      <div v-if="fileError[file.file_path]" style="margin-left: 24px; margin-top: 4px; color: #ef4444; font-size: 12px">
                        {{ fileError[file.file_path] }}
                      </div>

                      <!-- 展开的符号列表 -->
                      <div v-if="expandedFiles[file.file_path]" style="margin-left: 24px; margin-top: 4px">
                        <div
                          v-for="sym in expandedFiles[file.file_path]"
                          :key="sym.id"
                          @click="drawer.open(sym)"
                          style="display: flex; align-items: center; gap: 8px; padding: 4px 8px; border-radius: 4px; cursor: pointer; transition: background 0.15s"
                          class="sym-row"
                        >
                          <SymbolTag :kind="sym.kind" style="pointer-events: none" />
                          <span style="font-size: 13px; pointer-events: none">{{ sym.name }}</span>
                          <span style="font-size: 11px; color: #9ca3af; pointer-events: none">{{ sym.visibility }}</span>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>
              </template>
            </el-tab-pane>

            <!-- 依赖 Tab：首次切换时才请求数据（depsTabActivated 控制） -->
            <el-tab-pane label="依赖" name="deps">
              <div v-if="!deps" style="color: #9ca3af; text-align: center; padding: 24px">加载中...</div>
              <template v-else-if="!deps.sdk_deps || !deps.impl_deps">
                <!-- 旧格式缓存或数据异常，引导刷新 -->
                <el-empty description="依赖数据格式已更新，请重新选择模块" :image-size="80" />
              </template>
              <template v-else>
                <!-- 实现层依赖（Android 开发最常关注）-->
                <div style="margin-bottom: 20px">
                  <div style="font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px">
                    <span>实现层依赖</span>
                    <el-tag size="small" type="info">{{ deps.impl_deps.length }}</el-tag>
                    <span style="font-size: 11px; color: #9ca3af; font-weight: 400">来自 build.gradle</span>
                    <el-tag
                      v-if="deps.impl_deps.some(d => d.syntax === 'project')"
                      size="small" type="warning"
                    >⚠️ 含 project() 依赖</el-tag>
                  </div>
                  <div v-if="!deps.impl_deps.length" style="color: #9ca3af; font-size: 13px; padding: 4px 0">无</div>
                  <div v-else style="display: flex; flex-wrap: wrap; gap: 6px">
                    <div
                      v-for="d in deps.impl_deps"
                      :key="d.depends_on"
                      :style="{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '4px 10px', borderRadius: '6px', fontSize: '13px',
                        background: d.syntax === 'project' ? '#fffbeb' : '#f0fdf4',
                        border: d.syntax === 'project' ? '1px solid #fcd34d' : '1px solid #bbf7d0',
                      }"
                    >
                      <span :style="{ fontWeight: 500, color: d.syntax === 'project' ? '#92400e' : '#166534' }">
                        {{ d.depends_on }}
                      </span>
                      <el-tag size="small" :type="d.syntax === 'component' ? 'success' : 'warning'" style="font-size: 10px">
                        {{ d.syntax }}
                      </el-tag>
                      <span style="font-size: 11px; color: #6b7280">{{ d.scope }}</span>
                    </div>
                  </div>
                </div>

                <!-- 接口层依赖（SDK 接口对外声明的依赖，来自 component.gradle）-->
                <div>
                  <div style="font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px">
                    <span>接口层依赖</span>
                    <el-tag size="small" type="primary">{{ deps.sdk_deps.length }}</el-tag>
                    <span style="font-size: 11px; color: #9ca3af; font-weight: 400">来自 component.gradle</span>
                  </div>
                  <div v-if="!deps.sdk_deps.length" style="color: #9ca3af; font-size: 13px; padding: 4px 0">无</div>
                  <div v-else style="display: flex; flex-wrap: wrap; gap: 6px">
                    <div
                      v-for="d in deps.sdk_deps"
                      :key="d.depends_on"
                      style="display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; background: #eff6ff; border: 1px solid #bfdbfe; font-size: 13px"
                    >
                      <span style="font-weight: 500; color: #1d4ed8">{{ d.depends_on }}</span>
                      <el-tag size="small" type="primary" style="font-size: 10px">component</el-tag>
                      <span style="font-size: 11px; color: #6b7280">{{ d.scope }}</span>
                    </div>
                  </div>
                </div>
              </template>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </template>
    </div>
  </div>
</template>

<style scoped>
.sym-row:hover { background: #f3f4f6; }
.sym-row:active { background: #e5e7eb; }
.dir-row:hover { background: #eef2ff; }
</style>
