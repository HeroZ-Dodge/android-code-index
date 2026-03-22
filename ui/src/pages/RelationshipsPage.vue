<script setup lang="ts">
import { ref } from 'vue'
import { getInheritance, getSubclasses, getImplementations } from '@/api/symbols'
import { getModuleDeps } from '@/api/modules'
import { useDrawerStore } from '@/stores/drawer'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import type { Symbol } from '@/types'

use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer])

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

// ── Tab 3: 模块依赖图 ──
const moduleInput = ref('')
const graphOption = ref<any>(null)
const graphError = ref('')
const graphLoading = ref(false)

const colorMap: Record<string, string> = {}
const palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6']
let colorIdx = 0

function nodeColor(mod: string) {
  if (!colorMap[mod]) {
    colorMap[mod] = palette[colorIdx++ % palette.length]
  }
  return colorMap[mod]
}

async function loadDependencyGraph() {
  if (!moduleInput.value.trim()) return
  graphLoading.value = true
  graphError.value = ''
  try {
    const deps = await getModuleDeps(moduleInput.value.trim())
    const nodeSet = new Set<string>([moduleInput.value.trim()])
    deps.direct.forEach((d: { depends_on: string }) => nodeSet.add(d.depends_on))
    deps.indirect.forEach((d: { depends_on: string }) => nodeSet.add(d.depends_on))

    const nodes = [...nodeSet].map((n) => ({
      id: n,
      name: n,
      symbolSize: n === moduleInput.value.trim() ? 30 : 20,
      itemStyle: { color: nodeColor(n) },
    }))

    const edges = [
      ...deps.direct.map((d: { depends_on: string }) => ({
        source: moduleInput.value.trim(),
        target: d.depends_on,
        lineStyle: { width: 2 },
      })),
      ...deps.indirect.map((d: { depends_on: string }) => ({
        source: moduleInput.value.trim(),
        target: d.depends_on,
        lineStyle: { width: 1, type: 'dashed' as const, opacity: 0.5 },
      })),
    ]

    graphOption.value = {
      tooltip: { formatter: (p: any) => p.data.id ?? '' },
      series: [{
        type: 'graph',
        layout: 'force',
        force: { repulsion: 200, gravity: 0.1, edgeLength: 120 },
        roam: true,
        label: { show: true, fontSize: 10 },
        data: nodes,
        edges,
        edgeSymbol: ['none', 'arrow'],
      }],
    }
  } catch (e: any) {
    graphError.value = e?.message ?? '查询失败'
  } finally {
    graphLoading.value = false
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

      <!-- 模块依赖图 -->
      <el-tab-pane label="模块依赖图" name="deps">
        <el-row :gutter="12" style="margin-bottom: 16px">
          <el-col :span="16">
            <el-input v-model="moduleInput" placeholder="输入模块名（如 :app）" @keydown.enter="loadDependencyGraph" />
          </el-col>
          <el-col :span="8">
            <el-button type="primary" :loading="graphLoading" @click="loadDependencyGraph" style="width: 100%">生成依赖图</el-button>
          </el-col>
        </el-row>
        <el-alert v-if="graphError" :title="graphError" type="error" :closable="false" style="margin-bottom: 12px" />
        <v-chart v-if="graphOption" :option="graphOption" style="height: 500px" autoresize />
        <div v-else style="color: #9ca3af; text-align: center; padding: 48px">输入模块名后点击生成</div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>
