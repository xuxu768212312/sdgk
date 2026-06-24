<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Plan Review</h1>
        <p class="page-subtitle">梯度、概率、证据、闸门</p>
      </div>
      <StatusTag :value="job?.result?.hard_gate_passed" />
    </div>

    <el-alert
      v-if="!job"
      title="暂无方案"
      type="warning"
      show-icon
    />

    <template v-else>
      <div class="metrics">
        <div class="metric">
          <div class="metric-label">Selected</div>
          <div class="metric-value">{{ strategy?.selected_count ?? '-' }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Conservative Slip</div>
          <div class="metric-value">{{ strategy?.conservative_slip_probability ?? '-' }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Blocked</div>
          <div class="metric-value risk-block">{{ strategy?.blocked_count ?? '-' }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Formal</div>
          <div class="metric-value"><StatusTag :value="job.result?.hard_gate_passed" /></div>
        </div>
      </div>

      <div class="grid-2">
        <div class="panel">
          <h2 class="panel-title">Gradient</h2>
          <div ref="chartEl" class="chart"></div>
        </div>
        <div class="panel">
          <h2 class="panel-title">Violations</h2>
          <el-table :data="failures" height="280">
            <el-table-column prop="reason_code" label="reason_code" min-width="220" />
            <el-table-column prop="row" label="row" width="80" />
            <el-table-column prop="status" label="status" width="100" />
          </el-table>
        </div>
      </div>

      <div class="panel">
        <h2 class="panel-title">Selected Volunteers</h2>
        <el-table :data="strategy?.selected || []" height="560">
          <el-table-column prop="strategy_order" label="#" width="64" />
          <el-table-column prop="gradient_bucket" label="梯度" width="80" />
          <el-table-column prop="probability" label="概率" width="90" />
          <el-table-column prop="school_name" label="院校" min-width="160" />
          <el-table-column prop="major_name" label="专业" min-width="260" show-overflow-tooltip />
          <el-table-column prop="subject_check_status" label="选科" width="90">
            <template #default="{ row }"><StatusTag :value="row.subject_check_status" /></template>
          </el-table-column>
          <el-table-column prop="region_check_status" label="地区" width="90">
            <template #default="{ row }"><StatusTag :value="row.region_check_status" /></template>
          </el-table-column>
          <el-table-column prop="program_id" label="program_id" min-width="170" show-overflow-tooltip />
          <el-table-column prop="evidence_id" label="evidence_id" min-width="170" show-overflow-tooltip />
          <el-table-column prop="source_file" label="source_file" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import StatusTag from '../components/StatusTag.vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const job = computed(() => store.planJob)
const strategy = computed(() => job.value?.result?.strategy_result || null)
const failures = computed(() => job.value?.result?.final_audit?.failures || [])
const chartEl = ref<HTMLDivElement | null>(null)

function draw() {
  if (!chartEl.value || !strategy.value?.gradient_counts) return
  const counts = strategy.value.gradient_counts
  const chart = echarts.init(chartEl.value)
  chart.setOption({
    color: ['#d97706', '#1f5fbf', '#16803c', '#4b5563'],
    tooltip: {},
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        data: ['冲', '稳', '保', '垫'].map((name) => ({ name, value: counts[name] || 0 }))
      }
    ]
  })
}

onMounted(draw)
watch(job, async () => {
  await nextTick()
  draw()
})
</script>
