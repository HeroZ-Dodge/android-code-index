<script setup lang="ts">
import { ref, computed } from 'vue'
import client from '@/api/client'

const endpoints = [
  { label: 'GET /stats', path: '/stats', params: [] },
  { label: 'GET /stats/breakdown', path: '/stats/breakdown', params: [] },
  { label: 'GET /modules', path: '/modules', params: [] },
  { label: 'GET /search/code', path: '/search/code', params: [
    { name: 'keyword', type: 'string', required: true },
    { name: 'kind', type: 'string', required: false },
    { name: 'module', type: 'string', required: false },
    { name: 'use_tokens', type: 'boolean', required: false },
    { name: 'limit', type: 'number', required: false },
    { name: 'offset', type: 'number', required: false },
  ]},
  { label: 'GET /search/resource', path: '/search/resource', params: [
    { name: 'keyword', type: 'string', required: true },
    { name: 'kind', type: 'string', required: false },
    { name: 'module', type: 'string', required: false },
    { name: 'use_tokens', type: 'boolean', required: false },
    { name: 'limit', type: 'number', required: false },
    { name: 'offset', type: 'number', required: false },
  ]},
  { label: 'GET /modules/{module}/overview', path: '/modules/{module}/overview', params: [
    { name: 'module', type: 'string', required: true },
  ]},
  { label: 'GET /modules/{module}/dependencies', path: '/modules/{module}/dependencies', params: [
    { name: 'module', type: 'string', required: true },
  ]},
  { label: 'GET /modules/{module}/files', path: '/modules/{module}/files', params: [
    { name: 'module', type: 'string', required: true },
    { name: 'source_set', type: 'string', required: false },
  ]},
  { label: 'GET /symbols/class', path: '/symbols/class', params: [
    { name: 'name', type: 'string', required: false },
    { name: 'module', type: 'string', required: false },
    { name: 'limit', type: 'number', required: false },
  ]},
  { label: 'GET /resources/drawables', path: '/resources/drawables', params: [
    { name: 'name', type: 'string', required: false },
    { name: 'module', type: 'string', required: false },
    { name: 'limit', type: 'number', required: false },
  ]},
  { label: 'GET /resources/layouts', path: '/resources/layouts', params: [
    { name: 'name', type: 'string', required: false },
    { name: 'module', type: 'string', required: false },
    { name: 'limit', type: 'number', required: false },
  ]},
]

const selectedIdx = ref(0)
const selected = computed(() => endpoints[selectedIdx.value])
const paramValues = ref<Record<string, string>>({})

const loading = ref(false)
const responseTime = ref<number | null>(null)
const statusCode = ref<number | null>(null)
const responseBody = ref('')

async function send() {
  loading.value = true
  responseBody.value = ''
  statusCode.value = null
  responseTime.value = null

  let path = selected.value.path
  const queryParams: Record<string, string> = {}

  for (const p of selected.value.params) {
    const val = paramValues.value[p.name]?.trim()
    if (!val) continue
    if (path.includes(`{${p.name}}`)) {
      path = path.replace(`{${p.name}}`, encodeURIComponent(val))
    } else {
      queryParams[p.name] = val
    }
  }

  const t0 = Date.now()
  try {
    const res = await client.get(path, { params: queryParams })
    statusCode.value = res.status
    responseBody.value = JSON.stringify(res.data, null, 2)
  } catch (e: any) {
    statusCode.value = e.response?.status ?? 0
    responseBody.value = JSON.stringify(e.response?.data ?? { error: e.message }, null, 2)
  } finally {
    responseTime.value = Date.now() - t0
    loading.value = false
  }
}

function onEndpointChange() {
  paramValues.value = {}
  responseBody.value = ''
  statusCode.value = null
  responseTime.value = null
}
</script>

<template>
  <el-card shadow="never">
    <template #header>API Playground</template>

    <el-row :gutter="20">
      <!-- 左：端点选择 + 参数 -->
      <el-col :span="10">
        <div style="margin-bottom: 16px">
          <div style="font-weight: 600; margin-bottom: 8px">选择端点</div>
          <el-select
            v-model="selectedIdx"
            style="width: 100%"
            @change="onEndpointChange"
          >
            <el-option
              v-for="(ep, i) in endpoints"
              :key="i"
              :label="ep.label"
              :value="i"
            />
          </el-select>
        </div>

        <div v-if="selected.params.length">
          <div style="font-weight: 600; margin-bottom: 8px">参数</div>
          <div v-for="p in selected.params" :key="p.name" style="margin-bottom: 10px">
            <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px">
              {{ p.name }}
              <el-tag v-if="p.required" type="danger" size="small" style="margin-left: 4px">必填</el-tag>
            </div>
            <el-input
              v-model="paramValues[p.name]"
              :placeholder="`${p.type}`"
              size="small"
            />
          </div>
        </div>

        <el-button
          type="primary"
          :loading="loading"
          @click="send"
          style="width: 100%; margin-top: 8px"
        >
          发送请求
        </el-button>
      </el-col>

      <!-- 右：响应 -->
      <el-col :span="14">
        <div v-if="statusCode !== null" style="display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px">
          <span>
            状态码：
            <el-tag :type="statusCode >= 200 && statusCode < 300 ? 'success' : 'danger'" size="small">{{ statusCode }}</el-tag>
          </span>
          <span v-if="responseTime !== null">耗时：{{ responseTime }} ms</span>
        </div>
        <div v-if="responseBody">
          <div style="font-weight: 600; margin-bottom: 8px">响应</div>
          <pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; font-size: 12px; overflow: auto; max-height: 500px; white-space: pre-wrap; word-break: break-all">{{ responseBody }}</pre>
        </div>
        <div v-else style="color: #9ca3af; text-align: center; padding: 48px">
          选择端点并点击"发送请求"
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>
