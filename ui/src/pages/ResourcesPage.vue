<script setup lang="ts">
import { ref, reactive } from 'vue'
import { getLayouts, getStrings, getColors, getDimens, getStyles, getManifestComponents } from '@/api/resources'
import ColorSwatch from '@/components/ColorSwatch.vue'

const activeTab = ref('strings')

// ── Strings ──
const strFilter = reactive({ key: '', value: '', module: '' })
const strings = ref<any[]>([])
const strLoading = ref(false)
const strError = ref('')
async function loadStrings() {
  strLoading.value = true; strError.value = ''
  try { strings.value = await getStrings({ key: strFilter.key || undefined, value: strFilter.value || undefined, module: strFilter.module || undefined, limit: 50 }) }
  catch (e: any) { strError.value = e?.message ?? '加载失败' }
  finally { strLoading.value = false }
}

// ── Colors ──
const colorFilter = reactive({ name: '', module: '' })
const colors = ref<any[]>([])
const colorLoading = ref(false)
const colorError = ref('')
async function loadColors() {
  colorLoading.value = true; colorError.value = ''
  try { colors.value = await getColors({ name: colorFilter.name || undefined, module: colorFilter.module || undefined, limit: 50 }) }
  catch (e: any) { colorError.value = e?.message ?? '加载失败' }
  finally { colorLoading.value = false }
}

// ── Dimens ──
const dimenFilter = reactive({ name: '', module: '' })
const dimens = ref<any[]>([])
const dimenLoading = ref(false)
const dimenError = ref('')
async function loadDimens() {
  dimenLoading.value = true; dimenError.value = ''
  try { dimens.value = await getDimens({ name: dimenFilter.name || undefined, module: dimenFilter.module || undefined, limit: 50 }) }
  catch (e: any) { dimenError.value = e?.message ?? '加载失败' }
  finally { dimenLoading.value = false }
}

// ── Styles ──
const styleFilter = reactive({ name: '', module: '' })
const styles = ref<any[]>([])
const styleLoading = ref(false)
const styleError = ref('')
async function loadStyles() {
  styleLoading.value = true; styleError.value = ''
  try { styles.value = await getStyles({ name: styleFilter.name || undefined, module: styleFilter.module || undefined, limit: 50 }) }
  catch (e: any) { styleError.value = e?.message ?? '加载失败' }
  finally { styleLoading.value = false }
}

// ── Layouts ──
const layoutFilter = reactive({ name: '', module: '' })
const layouts = ref<any[]>([])
const layoutLoading = ref(false)
const layoutError = ref('')
async function loadLayouts() {
  layoutLoading.value = true; layoutError.value = ''
  try { layouts.value = await getLayouts({ name: layoutFilter.name || undefined, module: layoutFilter.module || undefined, limit: 50 }) }
  catch (e: any) { layoutError.value = e?.message ?? '加载失败' }
  finally { layoutLoading.value = false }
}

// ── Manifest ──
const manifestFilter = reactive({ component_type: '', module: '' })
const manifest = ref<any[]>([])
const manifestLoading = ref(false)
const manifestError = ref('')
async function loadManifest() {
  manifestLoading.value = true; manifestError.value = ''
  try { manifest.value = await getManifestComponents({ component_type: manifestFilter.component_type || undefined, module: manifestFilter.module || undefined, limit: 100 }) }
  catch (e: any) { manifestError.value = e?.message ?? '加载失败' }
  finally { manifestLoading.value = false }
}
</script>

<template>
  <el-card shadow="never">
    <el-tabs v-model="activeTab">

      <!-- Strings -->
      <el-tab-pane label="Strings" name="strings">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="8"><el-input v-model="strFilter.key" placeholder="key 过滤" clearable /></el-col>
          <el-col :span="8"><el-input v-model="strFilter.value" placeholder="value 过滤" clearable /></el-col>
          <el-col :span="6"><el-input v-model="strFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="2"><el-button type="primary" @click="loadStrings" :loading="strLoading">搜索</el-button></el-col>
        </el-row>
        <el-alert v-if="strError" :title="strError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="strings" size="small" stripe v-loading="strLoading">
          <el-table-column prop="name" label="key" />
          <el-table-column prop="resource_value" label="value" />
          <el-table-column prop="module" label="模块" width="160" />
        </el-table>
      </el-tab-pane>

      <!-- Colors -->
      <el-tab-pane label="Colors" name="colors">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="10"><el-input v-model="colorFilter.name" placeholder="名称过滤" clearable /></el-col>
          <el-col :span="10"><el-input v-model="colorFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="4"><el-button type="primary" @click="loadColors" :loading="colorLoading">搜索</el-button></el-col>
        </el-row>
        <el-alert v-if="colorError" :title="colorError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="colors" size="small" stripe v-loading="colorLoading">
          <el-table-column prop="name" label="名称" />
          <el-table-column label="色块 / 值" width="200">
            <template #default="{ row }"><ColorSwatch :value="row.resource_value" /></template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="160" />
        </el-table>
      </el-tab-pane>

      <!-- Dimens -->
      <el-tab-pane label="Dimens" name="dimens">
        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="10"><el-input v-model="dimenFilter.name" placeholder="名称过滤" clearable /></el-col>
          <el-col :span="10"><el-input v-model="dimenFilter.module" placeholder="模块" clearable /></el-col>
          <el-col :span="4"><el-button type="primary" @click="loadDimens" :loading="dimenLoading">搜索</el-button></el-col>
        </el-row>
        <el-alert v-if="dimenError" :title="dimenError" type="error" :closable="false" style="margin-bottom: 8px" />
        <el-table :data="dimens" size="small" stripe v-loading="dimenLoading">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="resource_value" label="值" width="120" />
          <el-table-column prop="module" label="模块" width="160" />
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
          <el-table-column prop="extra" label="类型" width="120">
            <template #default="{ row }">{{ row.extra ? JSON.parse(row.extra)?.component_type ?? '—' : '—' }}</template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="160" />
        </el-table>
      </el-tab-pane>

    </el-tabs>
  </el-card>
</template>
