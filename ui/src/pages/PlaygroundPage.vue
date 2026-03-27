<script setup lang="ts">
import { ref, computed } from 'vue'
import client from '@/api/client'

// 按功能分组，与 http_api.py 中所有端点一一对应
const endpointGroups = [
  {
    group: '统计',
    items: [
      { label: 'GET /stats', path: '/stats', params: [] },
      { label: 'GET /stats/breakdown', path: '/stats/breakdown', params: [] },
    ],
  },
  {
    group: '搜索',
    items: [
      { label: 'GET /search/code', path: '/search/code', params: [
        { name: 'keyword', type: 'string', required: true, placeholder: '如 FeedFragment' },
        { name: 'kind', type: 'string', required: false, placeholder: 'class | interface | function | property | object' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'use_tokens', type: 'string', required: false, placeholder: 'true | false' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
        { name: 'offset', type: 'number', required: false, placeholder: '默认 0' },
      ]},
      { label: 'GET /search/resource', path: '/search/resource', params: [
        { name: 'keyword', type: 'string', required: true, placeholder: '如 feed_item' },
        { name: 'kind', type: 'string', required: false, placeholder: 'layout | style | drawable | manifest_component' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'use_tokens', type: 'string', required: false, placeholder: 'true | false' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
        { name: 'offset', type: 'number', required: false, placeholder: '默认 0' },
      ]},
    ],
  },
  {
    group: '符号查询',
    items: [
      { label: 'GET /symbols/search/class', path: '/symbols/search/class', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 FeedFragment' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'parent_class', type: 'string', required: false, placeholder: '如 BaseFragment' },
        { name: 'annotation', type: 'string', required: false, placeholder: '如 HiltViewModel' },
        { name: 'source_set', type: 'string', required: false, placeholder: 'sdk | impl' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
        { name: 'offset', type: 'number', required: false, placeholder: '默认 0' },
      ]},
      { label: 'GET /symbols/search/function', path: '/symbols/search/function', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 onCreate' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'return_type', type: 'string', required: false, placeholder: '如 Boolean' },
        { name: 'visibility', type: 'string', required: false, placeholder: 'public | private | protected | internal' },
        { name: 'annotation', type: 'string', required: false, placeholder: '如 Override' },
        { name: 'source_set', type: 'string', required: false, placeholder: 'sdk | impl' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
        { name: 'offset', type: 'number', required: false, placeholder: '默认 0' },
      ]},
      { label: 'GET /symbols/search/interface', path: '/symbols/search/interface', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 IFeedService' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'source_set', type: 'string', required: false, placeholder: 'sdk | impl' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
        { name: 'offset', type: 'number', required: false, placeholder: '默认 0' },
      ]},
      { label: 'GET /files/{file_path}/symbols', path: '/files/{file_path}/symbols', params: [
        { name: 'file_path', type: 'string', required: true, placeholder: '如 compfeed/src/main/java/com/xxx/gl/compfeed/ad/AdDialogFrequencyLimitHelper.kt' },
      ]},
      { label: 'GET /files/{file_path}/imports', path: '/files/{file_path}/imports', params: [
        { name: 'file_path', type: 'string', required: true, placeholder: '如 compfeed/src/main/java/com/xxx/gl/compfeed/ad/AdDialogFrequencyLimitHelper.kt' },
      ]},
    ],
  },
  {
    group: '类关系',
    items: [
      { label: 'GET /classes/{class_name}/inheritance', path: '/classes/{class_name}/inheritance', params: [
        { name: 'class_name', type: 'string', required: true, placeholder: '如 FeedFragment' },
      ]},
      { label: 'GET /classes/{class_name}/subclasses', path: '/classes/{class_name}/subclasses', params: [
        { name: 'class_name', type: 'string', required: true, placeholder: '如 BaseFragment' },
        { name: 'direct_only', type: 'string', required: false, placeholder: 'true | false，默认 false' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 50' },
      ]},
      { label: 'GET /interfaces/{interface_name}/implementations', path: '/interfaces/{interface_name}/implementations', params: [
        { name: 'interface_name', type: 'string', required: true, placeholder: '如 IFeedService' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 50' },
      ]},
      { label: 'GET /classes/{class_name}/api', path: '/classes/{class_name}/api', params: [
        { name: 'class_name', type: 'string', required: true, placeholder: '如 FeedFragment' },
        { name: 'include_private', type: 'string', required: false, placeholder: 'true | false，默认 false' },
      ]},
      { label: 'GET /classes/{class_name}/api/full', path: '/classes/{class_name}/api/full', params: [
        { name: 'class_name', type: 'string', required: true, placeholder: '如 FeedFragment' },
        { name: 'include_private', type: 'string', required: false, placeholder: 'true | false，默认 false' },
      ]},
      { label: 'GET /symbols/{symbol_id}/source', path: '/symbols/{symbol_id}/source', params: [
        { name: 'symbol_id', type: 'string', required: true, placeholder: '如 145089' },
      ]},
    ],
  },
  {
    group: '模块',
    items: [
      { label: 'GET /modules', path: '/modules', params: [] },
      { label: 'GET /modules/{module}/overview', path: '/modules/{module}/overview', params: [
        { name: 'module', type: 'string', required: true, placeholder: '如 :compfeed' },
      ]},
      { label: 'GET /modules/{module}/files', path: '/modules/{module}/files', params: [
        { name: 'module', type: 'string', required: true, placeholder: '如 :compfeed' },
        { name: 'source_set', type: 'string', required: false, placeholder: 'sdk | impl' },
      ]},
      { label: 'GET /modules/{module}/dependencies', path: '/modules/{module}/dependencies', params: [
        { name: 'module', type: 'string', required: true, placeholder: '如 :compfeed' },
        { name: 'scope', type: 'string', required: false, placeholder: 'api | implementation | …' },
        { name: 'syntax', type: 'string', required: false, placeholder: 'component | project' },
      ]},
    ],
  },
  {
    group: '资源',
    items: [
      { label: 'GET /resources/layouts', path: '/resources/layouts', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 fragment_feed' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
      ]},
      { label: 'GET /resources/styles', path: '/resources/styles', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 AppTheme' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
      ]},
      { label: 'GET /resources/drawables', path: '/resources/drawables', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 ic_feed' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 50' },
      ]},
      { label: 'GET /manifest/components', path: '/manifest/components', params: [
        { name: 'name', type: 'string', required: false, placeholder: '如 FeedActivity' },
        { name: 'component_type', type: 'string', required: false, placeholder: 'activity | service | receiver | provider' },
        { name: 'module', type: 'string', required: false, placeholder: '如 :compfeed' },
        { name: 'limit', type: 'number', required: false, placeholder: '默认 20' },
      ]},
    ],
  },
]

// 展平为带分组标记的列表供 el-select 使用
const endpoints = endpointGroups.flatMap(g => g.items.map(item => ({ ...item, group: g.group })))

const selectedIdx = ref(0)
const selected = computed(() => endpoints[selectedIdx.value])
const paramValues = ref<Record<string, string>>({})

const loading = ref(false)
const responseTime = ref<number | null>(null)
const statusCode = ref<number | null>(null)
const responseBody = ref('')
const parsedItems = ref<any[]>([])
const expandedSrcCode = ref<Set<number>>(new Set())

// 检测响应是否为含 src_code 的符号列表
function extractItems(data: any): any[] {
  if (Array.isArray(data)) return data
  if (data && Array.isArray(data.items)) return data.items
  if (data && Array.isArray(data.members)) return data.members
  return []
}

function hasSrcCode(items: any[]): boolean {
  return items.some(item => item && typeof item.src_code === 'string' && item.src_code.length > 0)
}

function toggleSrcCode(idx: number) {
  if (expandedSrcCode.value.has(idx)) {
    expandedSrcCode.value.delete(idx)
  } else {
    expandedSrcCode.value.add(idx)
  }
}

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
    parsedItems.value = extractItems(res.data)
    expandedSrcCode.value = new Set()
  } catch (e: any) {
    statusCode.value = e.response?.status ?? 0
    responseBody.value = JSON.stringify(e.response?.data ?? { error: e.message }, null, 2)
    parsedItems.value = []
    expandedSrcCode.value = new Set()
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
  parsedItems.value = []
  expandedSrcCode.value = new Set()
}

function copyToClipboard(text: string) {
  window.navigator.clipboard.writeText(text)
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
            <el-option-group
              v-for="g in endpointGroups"
              :key="g.group"
              :label="g.group"
            >
              <el-option
                v-for="(ep, i) in endpoints"
                v-show="ep.group === g.group"
                :key="i"
                :label="ep.label"
                :value="i"
              />
            </el-option-group>
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
              :placeholder="p.placeholder ?? p.type"
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
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
            <span style="font-weight: 600">响应</span>
            <el-button size="small" @click="copyToClipboard(responseBody)">复制</el-button>
          </div>

          <!-- src_code 增强视图：当结果含有 src_code 时显示符号卡片 -->
          <template v-if="parsedItems.length > 0 && hasSrcCode(parsedItems)">
            <div
              v-for="(item, idx) in parsedItems"
              :key="idx"
              style="border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 8px; overflow: hidden"
            >
              <!-- 符号头部 -->
              <div
                style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #f9fafb; cursor: pointer"
                @click="item.src_code ? toggleSrcCode(idx) : null"
              >
                <div style="display: flex; align-items: center; gap: 8px; min-width: 0">
                  <el-tag size="small" type="info">{{ item.kind }}</el-tag>
                  <span style="font-weight: 600; font-size: 13px">{{ item.name }}</span>
                  <span v-if="item.module" style="font-size: 11px; color: #6b7280">{{ item.module }}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0">
                  <span v-if="item.return_type" style="font-size: 11px; color: #6b7280">→ {{ item.return_type }}</span>
                  <el-button
                    v-if="item.src_code"
                    size="small"
                    text
                    @click.stop="toggleSrcCode(idx)"
                  >
                    {{ expandedSrcCode.has(idx) ? '收起源码' : '查看源码' }}
                  </el-button>
                </div>
              </div>
              <!-- 源码展开区 -->
              <div v-if="item.src_code && expandedSrcCode.has(idx)">
                <pre style="margin: 0; padding: 12px 16px; background: #1e1e1e; color: #d4d4d4; font-size: 12px; overflow: auto; max-height: 400px; white-space: pre; word-break: normal">{{ item.src_code }}</pre>
              </div>
            </div>
          </template>

          <!-- 原始 JSON 视图 -->
          <div>
            <div
              style="font-size: 12px; color: #6b7280; margin-bottom: 4px; display: flex; align-items: center; gap: 8px"
              v-if="parsedItems.length > 0 && hasSrcCode(parsedItems)"
            >
              原始 JSON
            </div>
            <pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; font-size: 12px; overflow: auto; max-height: 400px; white-space: pre-wrap; word-break: break-all">{{ responseBody }}</pre>
          </div>
        </div>
        <div v-else style="color: #9ca3af; text-align: center; padding: 48px">
          选择端点并点击"发送请求"
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>
