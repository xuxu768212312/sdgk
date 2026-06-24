<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">方案复核</h1>
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
          <div class="metric-label">入选数量</div>
          <div class="metric-value">{{ strategy?.selected_count ?? '-' }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">保守滑档率</div>
          <div class="metric-value">{{ strategy?.conservative_slip_probability ?? '-' }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">阻断数量</div>
          <div class="metric-value risk-block">{{ strategy?.blocked_count ?? '-' }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">正式状态</div>
          <div class="metric-value"><StatusTag :value="job.result?.hard_gate_passed" /></div>
        </div>
      </div>

      <div class="grid-2">
        <div class="panel">
          <h2 class="panel-title">梯度结构</h2>
          <div ref="chartEl" class="chart"></div>
        </div>
        <div class="panel">
          <h2 class="panel-title">闸门问题</h2>
          <el-table :data="failures" height="280">
            <el-table-column label="原因" min-width="220">
              <template #default="{ row }">{{ reasonText(row.reason_code) }}</template>
            </el-table-column>
            <el-table-column prop="row" label="行号" width="80" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }"><StatusTag :value="row.status" /></template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="panel">
        <h2 class="panel-title">入选志愿</h2>
        <el-table :data="strategy?.selected || []" height="560">
          <el-table-column prop="strategy_order" label="序号" width="64" />
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
          <el-table-column prop="program_id" label="招生单元编号" min-width="170" show-overflow-tooltip />
          <el-table-column prop="evidence_id" label="证据编号" min-width="170" show-overflow-tooltip />
          <el-table-column prop="source_file" label="来源文件" min-width="220" show-overflow-tooltip />
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
const reasonLabels: Record<string, string> = {
  STRATEGY_HARD_GATE_FAILED: '策略硬闸门未通过',
  VOLUNTEER_COUNT_NOT_96: '志愿数量不足 96',
  SUBJECT_NOT_PASS: '选科未全部通过',
  REGION_NOT_RESOLVED: '地区偏好未全部确认',
  MISSING_REQUIRED_FIELDS: '缺少必填字段',
  DUPLICATE_VOLUNTEER: '存在重复志愿',
  MISSING_EVIDENCE: '缺少证据链',
  SLIP_PROBABILITY_TOO_HIGH: '滑档概率超限'
}

function reasonText(value?: string) {
  if (!value) return '无'
  return reasonLabels[value] || '未分类问题'
}

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
