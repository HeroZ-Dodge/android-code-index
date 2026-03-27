<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDrawerStore } from '@/stores/drawer'
import SymbolTag from './SymbolTag.vue'

const store = useDrawerStore()
const s = computed(() => store.symbol)

const expandedMemberIds = ref<Set<number>>(new Set())

async function toggleMember(id: number) {
  if (expandedMemberIds.value.has(id)) {
    expandedMemberIds.value = new Set([...expandedMemberIds.value].filter(x => x !== id))
  } else {
    await store.loadMemberSource(id)
    expandedMemberIds.value = new Set([...expandedMemberIds.value, id])
  }
}

function hasSrc(kind: string) {
  return kind === 'function' || kind === 'constructor'
}

function copyToClipboard(text: string) {
  window.navigator.clipboard.writeText(text)
}
</script>

<template>
  <el-drawer
    v-model="store.visible"
    title="符号详情"
    size="560px"
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

          <!-- 源码（function / constructor 自身，从搜索结果直接携带） -->
          <template v-if="(s.kind === 'function' || s.kind === 'constructor') && s.src_code">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">源码</div>
            <pre style="background: #1e1e1e; color: #d4d4d4; border-radius: 8px; padding: 14px 16px; font-size: 12px; overflow: auto; max-height: 480px; white-space: pre; word-break: normal; margin-bottom: 20px; line-height: 1.6">{{ s.src_code }}</pre>
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

          <!-- 成员列表（class/object），按需加载源码 -->
          <template v-if="store.members.length">
            <div style="margin-bottom: 8px; font-weight: 600; color: #374151">成员（{{ store.members.length }}）</div>
            <div
              v-for="member in store.members"
              :key="member.id"
              style="border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 6px; overflow: hidden"
            >
              <!-- 成员行 -->
              <div
                style="display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; background: #f9fafb"
                :style="hasSrc(member.kind) ? 'cursor: pointer' : ''"
                @click="hasSrc(member.kind) ? toggleMember(member.id) : null"
              >
                <div style="display: flex; align-items: center; gap: 8px; min-width: 0; overflow: hidden">
                  <SymbolTag :kind="member.kind" />
                  <span style="font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{ member.name }}</span>
                  <span v-if="member.return_type" style="font-size: 11px; color: #6b7280; white-space: nowrap">→ {{ member.return_type }}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0; margin-left: 8px">
                  <span style="font-size: 11px; color: #9ca3af">{{ member.visibility }}</span>
                  <el-button
                    v-if="hasSrc(member.kind)"
                    size="small" text type="primary"
                    :loading="store.memberSrcLoading.has(member.id)"
                    @click.stop="toggleMember(member.id)"
                  >{{ expandedMemberIds.has(member.id) ? '收起' : '源码' }}</el-button>
                </div>
              </div>
              <!-- 源码展开区（按需加载） -->
              <div v-if="expandedMemberIds.has(member.id)">
                <div v-if="store.memberSrcLoading.has(member.id)" style="padding: 12px 16px; color: #6b7280; font-size: 12px">
                  加载中...
                </div>
                <div v-else-if="store.memberSrcCache[member.id]">
                  <pre style="margin: 0; padding: 12px 16px; background: #1e1e1e; color: #d4d4d4; font-size: 12px; overflow: auto; max-height: 400px; white-space: pre; word-break: normal; line-height: 1.6">{{ store.memberSrcCache[member.id] }}</pre>
                </div>
                <div v-else style="padding: 12px 16px; color: #9ca3af; font-size: 12px">
                  暂无源码
                </div>
              </div>
            </div>
          </template>
        </div>
      </template>
    </el-skeleton>
  </el-drawer>
</template>
