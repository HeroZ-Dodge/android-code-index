<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useStatsStore } from '@/stores/stats'
import { use } from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const store = useStatsStore()

onMounted(() => store.load())

const langOption = computed(() => {
  const bd = store.breakdown
  if (!bd) return {}
  const entries = Object.entries(bd.by_language).sort((a, b) => b[1] - a[1]) as [string, number][]
  return {
    tooltip: { trigger: 'axis' as const },
    xAxis: { type: 'value' as const },
    yAxis: { type: 'category' as const, data: entries.map((e) => e[0]) },
    series: [{ type: 'bar' as const, data: entries.map((e) => e[1]), name: '文件数' }],
    grid: { left: 60, right: 20, top: 10, bottom: 10 },
  }
})

const kindOption = computed(() => {
  const bd = store.breakdown
  if (!bd) return {}
  const data = Object.entries(bd.by_kind)
    .sort((a, b) => (b[1] as number) - (a[1] as number))
    .map(([name, value]) => ({ name, value: value as number }))
  return {
    tooltip: { trigger: 'item' as const, formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical' as const, right: 10, top: 'center' as const },
    series: [{ type: 'pie' as const, radius: ['40%', '70%'], data, center: ['40%', '50%'] }],
  }
})
</script>

<template>
  <div>
    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    >
      <template #default>
        <el-button size="small" @click="store.load(true)">重试</el-button>
      </template>
    </el-alert>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="4" v-for="card in [
        { label: '文件数', value: store.stats?.total_files },
        { label: '符号数', value: store.stats?.total_symbols },
        { label: '模块数', value: store.stats?.modules },
        { label: '类数',   value: store.breakdown?.by_kind?.class },
        { label: '函数数', value: store.breakdown?.by_kind?.function },
        { label: '解析失败', value: store.stats?.parse_failures, warn: true },
      ]" :key="card.label">
        <el-card shadow="never">
          <el-skeleton :loading="store.loading" animated>
            <template #default>
              <div style="text-align: center">
                <div :style="{ fontSize: '28px', fontWeight: 700, color: card.warn && card.value ? '#ef4444' : '#2d3561' }">
                  {{ card.value ?? '—' }}
                </div>
                <div style="font-size: 13px; color: #6b7280; margin-top: 4px">{{ card.label }}</div>
              </div>
            </template>
          </el-skeleton>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="10">
        <el-card header="语言分布" shadow="never">
          <el-skeleton :loading="store.loading" animated>
            <template #default>
              <v-chart :option="langOption" style="height: 200px" autoresize />
            </template>
          </el-skeleton>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card header="符号类型分布" shadow="never">
          <el-skeleton :loading="store.loading" animated>
            <template #default>
              <v-chart :option="kindOption" style="height: 200px" autoresize />
            </template>
          </el-skeleton>
        </el-card>
      </el-col>
    </el-row>

    <!-- 模块排行 + 索引状态 -->
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card header="模块规模排行 Top 10" shadow="never">
          <el-skeleton :loading="store.loading" animated>
            <template #default>
              <el-table :data="store.breakdown?.module_ranking ?? []" size="small" stripe>
                <el-table-column type="index" label="#" width="40" />
                <el-table-column prop="module" label="模块" />
                <el-table-column prop="symbol_count" label="符号数" width="100" align="right" />
              </el-table>
            </template>
          </el-skeleton>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="索引状态" shadow="never">
          <el-skeleton :loading="store.loading" animated>
            <template #default>
              <div style="margin-bottom: 12px">
                <div style="font-size: 13px; color: #6b7280">最后索引时间</div>
                <div style="font-size: 14px; margin-top: 4px">{{ store.stats?.last_indexed || '—' }}</div>
              </div>
              <el-alert
                v-if="store.stats && store.stats.parse_failures > 0"
                :title="`${store.stats.parse_failures} 个文件解析失败`"
                type="warning"
                show-icon
                :closable="false"
              />
              <el-alert
                v-else-if="store.stats"
                title="所有文件解析成功"
                type="success"
                show-icon
                :closable="false"
              />
            </template>
          </el-skeleton>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
