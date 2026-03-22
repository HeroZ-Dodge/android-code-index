<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
  await store.selectModule(mod)
  router.replace({ path: `/modules/${encodeURIComponent(mod)}` })
}

// 文件树：每个文件的展开符号
const expandedFiles = ref<Record<string, Symbol[]>>({})
const loadingFile = ref<string | null>(null)

async function toggleFile(file: ModuleFile) {
  const key = file.file_path
  if (expandedFiles.value[key]) {
    delete expandedFiles.value[key]
    return
  }
  loadingFile.value = key
  try {
    // 去掉开头 / 以匹配路由路径格式
    const symbols = await getFileSymbols(file.file_path.replace(/^\//, ''))
    expandedFiles.value[key] = symbols
  } finally {
    loadingFile.value = null
  }
}

const activeTab = ref('files')

const overview = computed(() =>
  store.selectedModule ? store.overviewCache[store.selectedModule] : null
)
const deps = computed(() =>
  store.selectedModule ? store.depsCache[store.selectedModule] : null
)
const files = computed(() =>
  store.selectedModule ? store.filesCache[store.selectedModule] : null
)

const depSyntaxType = (syntax: string) =>
  syntax === 'component' ? 'primary' : syntax === 'project' ? 'warning' : 'info'
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
                style="padding: 10px 12px; border-radius: 8px; cursor: pointer; margin-bottom: 4px; transition: all 0.15s"
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
          <el-col :span="4" v-for="card in [
            { label: '文件数', value: overview?.files },
            { label: 'SDK 类', value: overview?.sdk_classes },
            { label: 'impl 类', value: overview?.impl_classes },
            { label: '接口', value: overview?.interfaces },
            { label: '函数', value: overview?.functions },
          ]" :key="card.label">
            <el-card shadow="never" body-style="padding: 12px; text-align: center">
              <div style="font-size: 22px; font-weight: 700; color: #2d3561">{{ card.value ?? '—' }}</div>
              <div style="font-size: 12px; color: #6b7280">{{ card.label }}</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Tab 区域 -->
        <el-card shadow="never">
          <el-tabs v-model="activeTab">
            <!-- 文件树 Tab -->
            <el-tab-pane label="文件树" name="files">
              <div v-if="!files" style="color: #9ca3af; text-align: center; padding: 24px">加载中...</div>
              <div v-else-if="!files.length" style="color: #9ca3af; text-align: center; padding: 24px">无文件</div>
              <template v-else>
                <div v-for="group in files" :key="group.dir_path" style="margin-bottom: 16px">
                  <div style="font-size: 12px; color: #6b7280; font-family: monospace; margin-bottom: 6px; padding: 4px 8px; background: #f8f9fc; border-radius: 4px">
                    {{ group.dir_path }}
                  </div>
                  <div
                    v-for="file in group.files"
                    :key="file.file_path"
                    style="margin-left: 16px; margin-bottom: 4px"
                  >
                    <div
                      @click="toggleFile(file)"
                      style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 6px; cursor: pointer; background: #fff; border: 1px solid #e5e7eb"
                    >
                      <el-icon :style="{ color: loadingFile === file.file_path ? '#9ca3af' : '#6b7280' }">
                        <component :is="expandedFiles[file.file_path] ? 'FolderOpened' : 'Document'" />
                      </el-icon>
                      <span style="font-family: monospace; font-size: 12px; flex: 1">
                        {{ file.file_path.split('/').pop() }}
                      </span>
                      <el-tag size="small" type="info">{{ file.file_type }}</el-tag>
                      <el-tag size="small">{{ file.symbol_count }}</el-tag>
                    </div>

                    <!-- 展开的符号列表 -->
                    <div v-if="expandedFiles[file.file_path]" style="margin-left: 24px; margin-top: 4px">
                      <div
                        v-for="sym in expandedFiles[file.file_path]"
                        :key="sym.id"
                        @click="drawer.open(sym)"
                        style="display: flex; align-items: center; gap: 8px; padding: 4px 8px; border-radius: 4px; cursor: pointer"
                        class="sym-row"
                      >
                        <SymbolTag :kind="sym.kind" />
                        <span style="font-size: 13px">{{ sym.name }}</span>
                        <span style="font-size: 11px; color: #9ca3af">{{ sym.visibility }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </el-tab-pane>

            <!-- 依赖 Tab -->
            <el-tab-pane label="依赖" name="deps">
              <div v-if="!deps" style="color: #9ca3af; text-align: center; padding: 24px">加载中...</div>
              <template v-else>
                <div style="margin-bottom: 16px">
                  <div style="font-weight: 600; margin-bottom: 8px">直接依赖（{{ deps.direct.length }}）</div>
                  <el-table :data="deps.direct" size="small" stripe>
                    <el-table-column prop="depends_on" label="依赖模块" />
                    <el-table-column label="类型" width="120">
                      <template #default="{ row }">
                        <el-tag :type="depSyntaxType(row.syntax)" size="small">{{ row.syntax }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="dependency_scope" label="scope" width="140" />
                  </el-table>
                </div>
                <div v-if="deps.indirect.length">
                  <el-collapse>
                    <el-collapse-item :title="`间接依赖（${deps.indirect.length}）`" name="indirect">
                      <el-table :data="deps.indirect" size="small" stripe>
                        <el-table-column prop="depends_on" label="模块" />
                        <el-table-column prop="depth" label="深度" width="80" />
                      </el-table>
                    </el-collapse-item>
                  </el-collapse>
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
</style>
