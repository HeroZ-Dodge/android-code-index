<script setup lang="ts">
import { useSearchStore } from '@/stores/search'
import { useDrawerStore } from '@/stores/drawer'
import SymbolTag from '@/components/SymbolTag.vue'
import type { Symbol } from '@/types'

const search = useSearchStore()
const drawer = useDrawerStore()

const kinds = [
  'class', 'interface', 'object', 'function', 'property',
  'layout', 'view_id', 'string_res', 'color_res', 'dimen_res',
  'style', 'manifest_component',
]

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function onKeywordChange() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    search.resetPage()
    search.doSearch()
  }, 300)
}

function onFilterChange() {
  search.resetPage()
  search.doSearch()
}

function onPageChange(page: number) {
  search.page = page
  search.doSearch()
}

function onSizeChange(size: number) {
  search.pageSize = size as 20 | 50 | 100
  search.resetPage()
  search.doSearch()
}
</script>

<template>
  <div>
    <!-- 搜索框 -->
    <el-card shadow="never" style="margin-bottom: 16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="10">
          <el-input
            v-model="search.keyword"
            placeholder="输入关键词搜索（支持驼峰、中文）"
            clearable
            @input="onKeywordChange"
            @clear="onKeywordChange"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="search.kindFilter" placeholder="全部类型" clearable @change="onFilterChange" style="width: 100%">
            <el-option v-for="k in kinds" :key="k" :label="k" :value="k" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input v-model="search.moduleFilter" placeholder="模块过滤（如 :app）" clearable @change="onFilterChange" />
        </el-col>
      </el-row>
    </el-card>

    <!-- 错误提示 -->
    <el-alert v-if="search.error" :title="search.error" type="error" show-icon :closable="false" style="margin-bottom: 16px">
      <template #default>
        <el-button size="small" @click="search.doSearch()">重试</el-button>
      </template>
    </el-alert>

    <!-- 结果表格 -->
    <el-card shadow="never">
      <div v-if="!search.keyword.trim()" style="color: #9ca3af; text-align: center; padding: 48px">
        输入关键词开始搜索
      </div>
      <template v-else>
        <div style="margin-bottom: 12px; font-size: 13px; color: #6b7280">
          共 {{ search.total }} 条结果
        </div>
        <el-table
          :data="search.results"
          v-loading="search.loading"
          stripe
          @row-click="(row: Symbol) => drawer.open(row)"
          style="cursor: pointer"
        >
          <el-table-column label="类型" width="130">
            <template #default="{ row }">
              <SymbolTag :kind="row.kind" />
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column label="qualified_name" min-width="240">
            <template #default="{ row }">
              <el-text style="font-family: monospace; font-size: 12px; word-break: break-all">
                {{ row.qualified_name }}
              </el-text>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="160" />
          <el-table-column prop="line_number" label="行号" width="80" align="right">
            <template #default="{ row }">{{ row.line_number ?? '—' }}</template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="search.total > 0"
          v-model:current-page="search.page"
          v-model:page-size="search.pageSize"
          :page-sizes="[20, 50, 100]"
          :total="search.total"
          layout="total, sizes, prev, pager, next"
          @current-change="onPageChange"
          @size-change="onSizeChange"
          style="margin-top: 16px; justify-content: flex-end"
        />
      </template>
    </el-card>
  </div>
</template>
