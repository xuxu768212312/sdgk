<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">数据审计、索引规模、方案闸门</p>
      </div>
      <div class="toolbar">
        <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
      </div>
    </div>

    <div class="metrics">
      <div class="metric">
        <div class="metric-label">API</div>
        <div class="metric-value"><StatusTag :value="health?.status" /></div>
      </div>
      <div class="metric">
        <div class="metric-label">Master Programs</div>
        <div class="metric-value">{{ summary?.master_index?.counts?.programs ?? '-' }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Admission History</div>
        <div class="metric-value">{{ summary?.master_index?.counts?.admission_history ?? '-' }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Audit</div>
        <div class="metric-value"><StatusTag :value="audit?.status" /></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h2 class="panel-title">Index Counts</h2>
        <div ref="chartEl" class="chart"></div>
      </div>
      <div class="panel">
        <h2 class="panel-title">Gate Snapshot</h2>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Subject Index"><StatusTag :value="summary?.subject_index?.exists" /></el-descriptions-item>
          <el-descriptions-item label="Region Index"><StatusTag :value="summary?.region_index?.exists" /></el-descriptions-item>
          <el-descriptions-item label="Master Index"><StatusTag :value="summary?.master_index?.exists" /></el-descriptions-item>
          <el-descriptions-item label="Latest Audit">{{ audit?.latest_report || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import { getAuditStatus, getHealth, getIndexSummary } from '../api/client'

const loading = ref(false)
const health = ref<any>(null)
const summary = ref<any>(null)
const audit = ref<any>(null)
const chartEl = ref<HTMLDivElement | null>(null)

function drawChart() {
  if (!chartEl.value || !summary.value?.master_index?.counts) return
  const counts = summary.value.master_index.counts
  const chart = echarts.init(chartEl.value)
  chart.setOption({
    color: ['#1f5fbf'],
    tooltip: {},
    grid: { left: 48, right: 12, top: 12, bottom: 48 },
    xAxis: { type: 'category', data: ['schools', 'majors', 'programs', 'admission', 'plans'] },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: [counts.schools, counts.majors, counts.programs, counts.admission_history, counts.plan_history],
        barWidth: 26
      }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    const [h, s, a] = await Promise.all([getHealth(), getIndexSummary(), getAuditStatus()])
    health.value = h
    summary.value = s
    audit.value = a
    await nextTick()
    drawChart()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
