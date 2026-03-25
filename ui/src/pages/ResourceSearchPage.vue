<script setup lang="ts">
import { ref } from 'vue'
import { searchResource } from '@/api/search'
import { useDrawerStore } from '@/stores/drawer'
import SymbolTag from '@/components/SymbolTag.vue'
import type { Symbol } from '@/types'

const drawer = useDrawerStore()

const kinds = ['layout', 'style', 'manifest_component', 'drawable']

const keyword = ref('')
const kindFilter = ref<string | null>(null)
const moduleFilter = ref<string | null>(null)
const useTokens = ref(true)
const results = ref<Symbol[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref<20 | 50 | 100>(20)
const loading = ref(false)
const error = ref<string | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

async function doSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  error.value = null
  try {
    const res = await searchResource({
      keyword: keyword.value,
      kind: kindFilter.value || undefined,
      module: moduleFilter.value || undefined,
      use_tokens: useTokens.value,
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    })
    results.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e?.message ?? '搜索失败'
  } finally {
    loading.value = false
  }
}

function onKeywordChange() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    doSearch()
  }, 300)
}

function onFilterChange() {
  page.value = 1
  doSearch()
}

function onPageChange(p: number) {
  page.value = p
  doSearch()
}

function onSizeChange(size: number) {
  pageSize.value = size as 20 | 50 | 100
  page.value = 1
  doSearch()
}
</script>

<template>
  <div>
    <!-- 搜索框 -->
    <el-card shadow="never" style="margin-bottom: 16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="9">
          <el-input
            v-model="keyword"
            placeholder="输入关键词搜索资源（layout/style/drawable/manifest）"
            clearable
            @input="onKeywordChange"
            @clear="onKeywordChange"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="5">
          <el-select v-model="kindFilter" placeholder="全部类型" clearable @change="onFilterChange" style="width: 100%">
            <el-option v-for="k in kinds" :key="k" :label="k" :value="k" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="moduleFilter" placeholder="模块过滤（如 :app）" clearable @change="onFilterChange" />
        </el-col>
        <el-col :span="4">
          <el-switch
            v-model="useTokens"
            active-text="分词匹配"
            inactive-text=""
            @change="onFilterChange"
          />
        </el-col>
      </el-row>
    </el-card>

    <!-- 错误提示 -->
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" style="margin-bottom: 16px">
      <template #default>
        <el-button size="small" @click="doSearch()">重试</el-button>
      </template>
    </el-alert>

    <!-- 结果表格 -->
    <el-card shadow="never">
      <div v-if="!keyword.trim()" style="color: #9ca3af; text-align: center; padding: 48px">
        输入关键词开始搜索
      </div>
      <template v-else>
        <div style="margin-bottom: 12px; font-size: 13px; color: #6b7280">
          共 {{ total }} 条结果
        </div>
        <el-table
          :data="results"
          v-loading="loading"
          stripe
          @row-click="(row: Symbol) => drawer.open(row)"
          style="cursor: pointer"
        >
          <el-table-column label="类型" width="150">
            <template #default="{ row }">
              <SymbolTag :kind="row.kind" />
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="resource_value" label="值/类型" min-width="120">
            <template #default="{ row }">{{ row.resource_value ?? '—' }}</template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="160" />
          <el-table-column prop="file_path" label="文件路径" min-width="200">
            <template #default="{ row }">
              <el-text style="font-family: monospace; font-size: 11px; word-break: break-all">
                {{ row.file_path }}
              </el-text>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="total > 0"
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="onPageChange"
          @size-change="onSizeChange"
          style="margin-top: 16px; justify-content: flex-end"
        />
      </template>
    </el-card>
  </div>
</template>
