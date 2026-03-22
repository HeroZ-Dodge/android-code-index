<script setup lang="ts">
import { computed } from 'vue'
import { useDrawerStore } from '@/stores/drawer'
import SymbolTag from './SymbolTag.vue'

const store = useDrawerStore()
const s = computed(() => store.symbol)

function copyToClipboard(text: string) {
  window.navigator.clipboard.writeText(text)
}
</script>

<template>
  <el-drawer
    v-model="store.visible"
    title="符号详情"
    size="480px"
    :destroy-on-close="false"
  >
    <el-skeleton :loading="store.loading" animated>
      <template #default>
        <div v-if="s" style="padding: 0 4px">
          <!-- 基本信息 -->
          <el-descriptions :column="1" border size="small" style="margin-bottom: 20px">
            <el-descriptions-item label="名称">
              <strong>{{ s.name }}</strong>
            </el-descriptions-item>
            <el-descriptions-item label="类型">
              <SymbolTag :kind="s.kind" />
            </el-descriptions-item>
            <el-descriptions-item label="qualified_name">
              <el-text type="info" style="font-family: monospace; font-size: 12px; word-break: break-all">
                {{ s.qualified_name }}
              </el-text>
              <el-button
                link type="primary" size="small"
                @click="copyToClipboard(s.qualified_name)"
                style="margin-left: 4px"
              >复制</el-button>
            </el-descriptions-item>
            <el-descriptions-item label="模块">{{ s.module }}</el-descriptions-item>
            <el-descriptions-item label="可见性">{{ s.visibility || '—' }}</el-descriptions-item>
            <el-descriptions-item label="文件">
              <el-text style="font-family: monospace; font-size: 11px; word-break: break-all">{{ s.file_path }}</el-text>
            </el-descriptions-item>
            <el-descriptions-item label="行号">{{ s.line_number ?? '—' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 签名 -->
          <template v-if="s.signature">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">签名</div>
            <pre style="background: #f8f9fc; border-radius: 8px; padding: 12px; font-size: 12px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; margin-bottom: 20px">{{ s.signature }}</pre>
          </template>

          <!-- 继承链 (class) -->
          <template v-if="(s.kind === 'class' || s.kind === 'object') && store.inheritanceChain.length">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">继承链</div>
            <el-breadcrumb separator="›" style="margin-bottom: 20px">
              <el-breadcrumb-item v-for="c in store.inheritanceChain" :key="c">{{ c }}</el-breadcrumb-item>
            </el-breadcrumb>
          </template>

          <!-- 子类 (class) -->
          <template v-if="(s.kind === 'class' || s.kind === 'object') && store.subclasses.length">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">子类（{{ store.subclasses.length }}）</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px">
              <el-tag v-for="sub in store.subclasses" :key="sub.id" type="info" size="small">{{ sub.name }}</el-tag>
            </div>
          </template>

          <!-- 接口实现者 (interface) -->
          <template v-if="s.kind === 'interface' && store.implementations.length">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">实现类（{{ store.implementations.length }}）</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px">
              <el-tag v-for="impl in store.implementations" :key="impl.id" type="success" size="small">{{ impl.name }}</el-tag>
            </div>
          </template>

          <!-- 成员列表 -->
          <template v-if="store.members.length">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">成员（{{ store.members.length }}）</div>
            <el-table :data="store.members" size="small" stripe style="width: 100%">
              <el-table-column label="类型" width="90">
                <template #default="{ row }">
                  <SymbolTag :kind="row.kind" />
                </template>
              </el-table-column>
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="visibility" label="可见性" width="80" />
            </el-table>
          </template>
        </div>
      </template>
    </el-skeleton>
  </el-drawer>
</template>
