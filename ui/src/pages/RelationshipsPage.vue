<script setup lang="ts">
import { ref } from 'vue'
import { getInheritance, getSubclasses, getImplementations } from '@/api/symbols'
import { getModuleDeps } from '@/api/modules'
import { useDrawerStore } from '@/stores/drawer'
import type { Symbol, ModuleDeps } from '@/types'

const drawer = useDrawerStore()
const activeTab = ref('inheritance')

// ── Tab 1: 继承链 ──
const classInput = ref('')
const inheritanceChain = ref<string[]>([])
const subclasses = ref<Symbol[]>([])
const inheritanceError = ref('')
const inheritanceLoading = ref(false)

async function loadInheritance() {
  if (!classInput.value.trim()) return
  inheritanceLoading.value = true
  inheritanceError.value = ''
  try {
    const [chain, subs] = await Promise.all([
      getInheritance(classInput.value.trim()),
      getSubclasses(classInput.value.trim()),
    ])
    inheritanceChain.value = chain
    subclasses.value = subs
  } catch (e: any) {
    inheritanceError.value = e?.message ?? '查询失败'
  } finally {
    inheritanceLoading.value = false
  }
}

// ── Tab 2: 接口实现 ──
const ifaceInput = ref('')
const implementations = ref<Symbol[]>([])
const ifaceError = ref('')
const ifaceLoading = ref(false)

async function loadImplementations() {
  if (!ifaceInput.value.trim()) return
  ifaceLoading.value = true
  ifaceError.value = ''
  try {
    implementations.value = await getImplementations(ifaceInput.value.trim())
  } catch (e: any) {
    ifaceError.value = e?.message ?? '查询失败'
  } finally {
    ifaceLoading.value = false
  }
}

// ── Tab 3: 模块依赖 ──
const moduleInput = ref('')
const moduleDeps = ref<ModuleDeps | null>(null)
const queriedModule = ref('')
const depsError = ref('')
const depsLoading = ref(false)

async function loadDependencyGraph() {
  const mod = moduleInput.value.trim()
  if (!mod) return
  depsLoading.value = true
  depsError.value = ''
  moduleDeps.value = null
  try {
    moduleDeps.value = await getModuleDeps(mod)
    queriedModule.value = mod
  } catch (e: any) {
    depsError.value = e?.message ?? '查询失败'
  } finally {
    depsLoading.value = false
  }
}
</script>

<template>
  <el-card shadow="never">
    <el-tabs v-model="activeTab">
      <!-- 继承链 -->
      <el-tab-pane label="继承链" name="inheritance">
        <el-row :gutter="12" style="margin-bottom: 16px">
          <el-col :span="16">
            <el-input
              v-model="classInput"
              placeholder="输入类名（如 BaseActivity）"
              @keydown.enter="loadInheritance"
            />
          </el-col>
          <el-col :span="8">
            <el-button type="primary" :loading="inheritanceLoading" @click="loadInheritance" style="width: 100%">查询</el-button>
          </el-col>
        </el-row>
        <el-alert v-if="inheritanceError" :title="inheritanceError" type="error" :closable="false" style="margin-bottom: 12px" />
        <template v-if="inheritanceChain.length">
          <div style="margin-bottom: 16px">
            <div style="font-weight: 600; margin-bottom: 8px; color: #374151">继承链（向上）</div>
            <el-breadcrumb separator="→">
              <el-breadcrumb-item v-for="c in inheritanceChain" :key="c">{{ c }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div v-if="subclasses.length">
            <div style="font-weight: 600; margin-bottom: 8px; color: #374151">直接子类（{{ subclasses.length }}）</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px">
              <el-tag
                v-for="s in subclasses"
                :key="s.id"
                type="info"
                style="cursor: pointer"
                @click="drawer.open(s)"
              >{{ s.name }}</el-tag>
            </div>
          </div>
        </template>
      </el-tab-pane>

      <!-- 接口实现 -->
      <el-tab-pane label="接口实现" name="interface">
        <el-row :gutter="12" style="margin-bottom: 16px">
          <el-col :span="16">
            <el-input v-model="ifaceInput" placeholder="输入接口名" @keydown.enter="loadImplementations" />
          </el-col>
          <el-col :span="8">
            <el-button type="primary" :loading="ifaceLoading" @click="loadImplementations" style="width: 100%">查询</el-button>
          </el-col>
        </el-row>
        <el-alert v-if="ifaceError" :title="ifaceError" type="error" :closable="false" style="margin-bottom: 12px" />
        <el-table v-if="implementations.length" :data="implementations" size="small" stripe>
          <el-table-column prop="name" label="实现类" />
          <el-table-column prop="module" label="模块" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="drawer.open(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 模块依赖 -->
      <el-tab-pane label="模块依赖" name="deps">
        <el-row :gutter="12" style="margin-bottom: 16px">
          <el-col :span="16">
            <el-input v-model="moduleInput" placeholder="输入模块名（如 compfeed）" @keydown.enter="loadDependencyGraph" />
          </el-col>
          <el-col :span="8">
            <el-button type="primary" :loading="depsLoading" @click="loadDependencyGraph" style="width: 100%">查询依赖</el-button>
          </el-col>
        </el-row>
        <el-alert v-if="depsError" :title="depsError" type="error" :closable="false" style="margin-bottom: 12px" />

        <div v-if="moduleDeps" class="dep-tree">
          <!-- 根节点：被查询的模块 -->
          <div class="dep-root">
            <span class="dep-module-name">{{ queriedModule }}</span>
            <el-tag size="small" type="info" style="margin-left: 8px">
              {{ moduleDeps.impl_deps.length + moduleDeps.sdk_deps.length }} 个依赖
            </el-tag>
          </div>

          <!-- 实现层依赖 -->
          <div class="dep-section">
            <div class="dep-section-header" :class="moduleDeps.sdk_deps.length ? 'has-sibling' : 'last-child'">
              <span class="dep-branch-line"></span>
              <span class="dep-section-title">实现层依赖</span>
              <span class="dep-section-meta">build.gradle · {{ moduleDeps.impl_deps.length }} 个</span>
              <el-tag v-if="moduleDeps.impl_deps.some(d => d.syntax === 'project')" size="small" type="warning" style="margin-left: 6px">⚠ 含 project()</el-tag>
            </div>
            <div class="dep-section-body" :class="moduleDeps.sdk_deps.length ? 'has-sibling' : ''">
              <div v-if="!moduleDeps.impl_deps.length" class="dep-empty">无</div>
              <div
                v-for="(d, i) in moduleDeps.impl_deps"
                :key="d.depends_on"
                class="dep-item"
                :class="i === moduleDeps.impl_deps.length - 1 ? 'last' : ''"
              >
                <span class="dep-item-line"></span>
                <span class="dep-item-name" :class="d.syntax === 'project' ? 'is-project' : ''">{{ d.depends_on }}</span>
                <el-tag
                  size="small"
                  :type="d.syntax === 'component' ? 'success' : 'warning'"
                  style="margin-left: 8px; font-size: 10px"
                >{{ d.syntax }}</el-tag>
                <span v-if="d.syntax === 'project'" style="margin-left: 4px; font-size: 11px; color: #f59e0b">⚠</span>
              </div>
            </div>
          </div>

          <!-- 接口层依赖 -->
          <div class="dep-section dep-section-last">
            <div class="dep-section-header last-child">
              <span class="dep-branch-line last"></span>
              <span class="dep-section-title">接口层依赖</span>
              <span class="dep-section-meta">component.gradle · {{ moduleDeps.sdk_deps.length }} 个</span>
            </div>
            <div class="dep-section-body">
              <div v-if="!moduleDeps.sdk_deps.length" class="dep-empty">无</div>
              <div
                v-for="(d, i) in moduleDeps.sdk_deps"
                :key="d.depends_on"
                class="dep-item"
                :class="i === moduleDeps.sdk_deps.length - 1 ? 'last' : ''"
              >
                <span class="dep-item-line"></span>
                <span class="dep-item-name">{{ d.depends_on }}</span>
                <el-tag size="small" type="primary" style="margin-left: 8px; font-size: 10px">component</el-tag>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="!depsLoading" style="color: #9ca3af; text-align: center; padding: 48px; font-size: 13px">
          输入模块名后点击查询
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.dep-tree {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  padding: 16px 8px;
  line-height: 1.8;
}

.dep-root {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: #f0f4ff;
  border: 1px solid #c7d2fe;
  border-radius: 6px;
  margin-bottom: 4px;
}

.dep-module-name {
  font-weight: 700;
  color: #2d3561;
  font-size: 14px;
}

.dep-section {
  margin-left: 16px;
}

.dep-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  color: #374151;
  font-weight: 600;
  font-size: 12px;
  position: relative;
}

.dep-section-header::before {
  content: '├─';
  color: #9ca3af;
  font-family: monospace;
  margin-right: 4px;
}

.dep-section-header.last-child::before {
  content: '└─';
}

.dep-branch-line { display: none; }

.dep-section-title {
  color: #1f2937;
}

.dep-section-meta {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 400;
}

.dep-section-body {
  margin-left: 20px;
  border-left: 1px dashed #e5e7eb;
  padding-left: 12px;
  margin-bottom: 8px;
}

.dep-empty {
  color: #9ca3af;
  font-size: 12px;
  padding: 2px 0;
}

.dep-item {
  display: flex;
  align-items: center;
  padding: 3px 0;
  position: relative;
}

.dep-item::before {
  content: '├─';
  color: #9ca3af;
  margin-right: 6px;
  font-family: monospace;
}

.dep-item.last::before {
  content: '└─';
}

.dep-item-line { display: none; }

.dep-item-name {
  color: #1d4ed8;
  font-weight: 500;
}

.dep-item-name.is-project {
  color: #92400e;
}
</style>
