<script setup lang="ts">
import { ref, reactive } from 'vue'
import { getLayouts, getStyles, getDrawables, getManifestComponents } from '@/api/resources'

const activeTab = ref('layouts')

// ── Layouts ──
const layoutFilter = reactive({ name: '', module: '' })
const layouts = ref<any[]>([])
const layoutLoading = ref(false)
const layoutError = ref('')
async function loadLayouts() {
  layoutLoading.value = true; layoutError.value = ''
  try { layouts.value = (await getLayouts({ name: layoutFilter.name || undefined, module: layoutFilter.module || undefined, limit: 50 })).items }
  catch (e: any) { layoutError.value = e?.message ?? '加载失败' }
  finally { layoutLoading.value = false }
}

// ── Styles ──
const styleFilter = reactive({ name: '', module: '' })
const styles = ref<any[]>([])
const styleLoading = ref(false)
const styleError = ref('')
async function loadStyles() {
  styleLoading.value = true; styleError.value = ''
  try { styles.value = (await getStyles({ name: styleFilter.name || undefined, module: styleFilter.module || undefined, limit: 50 })).items }
  catch (e: any) { styleError.value = e?.message ?? '加载失败' }
  finally { styleLoading.value = false }
}

// ── Drawables ──
const drawableFilter = reactive({ name: '', module: '' })
const drawables = ref<any[]>([])
const drawableLoading = ref(false)
const drawableError = ref('')
async function loadDrawables() {
  drawableLoading.value = true; drawableError.value = ''
  try { drawables.value = (await getDrawables({ name: drawableFilter.name || undefined, module: drawableFilter.module || undefined, limit: 100 })).items }
  catch (e: any) { drawableError.value = e?.message ?? '加载失败' }
  finally { drawableLoading.value = false }
}

// ── Manifest ──
const manifestFilter = reactive({ component_type: '', module: '' })
const manifest = ref<any[]>([])
const manifestLoading = ref(false)
const manifestError = ref('')
async function loadManifest() {
  manifestLoading.value = true; manifestError.value = ''
  try { manifest.value = (await getManifestComponents({ component_type: manifestFilter.component_type || undefined, module: manifestFilter.module || undefined, limit: 100 })).items }
  catch (e: any) { manifestError.value = e?.message ?? '加载失败' }
  finally { manifestLoading.value = false }
}
</script>

<template>
  <el-card shadow="never">
    <el-tabs v-model="activeTab">

      <!-- Layouts -->
      <el-tab-pane label="Layouts" name="layouts">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="10"><el-input v-model="layoutFilter.name" placeholder="名称过滤" clearable /></el-col>
          <el-col :span="10"><el-input v-model="layoutFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="4"><el-button type="primary" @click="loadLayouts" :loading="layoutLoading">搜索</el-button></el-col>
        </el-row>
        <el-alert v-if="layoutError" :title="layoutError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="layouts" size="small" stripe v-loading="layoutLoading">
          <el-table-column prop="name" label="文件名" />
          <el-table-column prop="module" label="模块" width="160" />
          <el-table-column prop="extra" label="根布局" width="140">
            <template #default="{ row }">{{ row.extra ? JSON.parse(row.extra)?.root_view ?? '—' : '—' }}</template>
          </el-table-column>
          <el-table-column prop="file_path" label="路径" min-width="200">
            <template #default="{ row }">
              <el-text style="font-family: monospace; font-size: 11px; word-break: break-all">{{ row.file_path }}</el-text>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Styles -->
      <el-tab-pane label="Styles" name="styles">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="10"><el-input v-model="styleFilter.name" placeholder="名称过滤" clearable /></el-col>
          <el-col :span="10"><el-input v-model="styleFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="4"><el-button type="primary" @click="loadStyles" :loading="styleLoading">搜索</el-button></el-col>
        </el-row>
        <el-alert v-if="styleError" :title="styleError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="styles" size="small" stripe v-loading="styleLoading">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="parent_class" label="parent" />
          <el-table-column prop="module" label="模块" width="160" />
        </el-table>
      </el-tab-pane>

      <!-- Drawables -->
      <el-tab-pane label="Drawables" name="drawables">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="10"><el-input v-model="drawableFilter.name" placeholder="名称过滤" clearable /></el-col>
          <el-col :span="10"><el-input v-model="drawableFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="4"><el-button type="primary" @click="loadDrawables" :loading="drawableLoading">搜索</el-button></el-col>
        </el-row>
        <el-alert v-if="drawableError" :title="drawableError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="drawables" size="small" stripe v-loading="drawableLoading">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="resource_value" label="类型" width="120" />
          <el-table-column prop="module" label="模块" width="160" />
          <el-table-column prop="file_path" label="路径" min-width="200">
            <template #default="{ row }">
              <el-text style="font-family: monospace; font-size: 11px; word-break: break-all">{{ row.file_path }}</el-text>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Manifest -->
      <el-tab-pane label="Manifest" name="manifest">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="10">
            <el-select v-model="manifestFilter.component_type" placeholder="组件类型" clearable style="width: 100%">
              <el-option label="Activity" value="activity" />
              <el-option label="Service" value="service" />
              <el-option label="BroadcastReceiver" value="receiver" />
              <el-option label="ContentProvider" value="provider" />
            </el-select>
          </el-col>
          <el-col :span="10"><el-input v-model="manifestFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="4"><el-button type="primary" @click="loadManifest" :loading="manifestLoading">查询</el-button></el-col>
        </el-row>
        <el-alert v-if="manifestError" :title="manifestError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="manifest" size="small" stripe v-loading="manifestLoading">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="annotations" label="类型" width="120">
            <template #default="{ row }">{{ row.annotations ? JSON.parse(row.annotations)[0] ?? '—' : '—' }}</template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="160" />
        </el-table>
      </el-tab-pane>

    </el-tabs>
  </el-card>
</template>
