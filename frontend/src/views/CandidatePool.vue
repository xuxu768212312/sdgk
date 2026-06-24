<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">候选池</h1>
        <p class="page-subtitle">通过候选与复核清单</p>
      </div>
      <div class="toolbar">
        <el-switch v-model="hardRegion" active-text="硬地区" inactive-text="软地区" />
        <el-button type="primary" :icon="Filter" :loading="loading" @click="run">生成候选池</el-button>
      </div>
    </div>

    <div class="metrics">
      <div class="metric">
        <div class="metric-label">通过候选</div>
        <div class="metric-value">{{ pool?.counts?.candidates ?? '-' }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">待复核</div>
        <div class="metric-value risk-review">{{ pool?.counts?.review ?? '-' }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">阻断</div>
        <div class="metric-value risk-block">{{ pool?.counts?.blocked ?? '-' }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">模拟状态</div>
        <div class="metric-value"><StatusTag :value="pool?.simulation" /></div>
      </div>
    </div>

    <div class="panel">
      <h2 class="panel-title">候选志愿</h2>
      <el-table :data="pool?.candidates || []" height="560">
        <el-table-column prop="probability" label="概率" width="90" sortable />
        <el-table-column prop="school_name" label="院校" min-width="170" />
        <el-table-column prop="major_name" label="专业" min-width="260" show-overflow-tooltip />
        <el-table-column prop="major_family" label="标签" width="110" />
        <el-table-column prop="province" label="省份" width="90" />
        <el-table-column prop="subject_check_status" label="选科" width="90">
          <template #default="{ row }"><StatusTag :value="row.subject_check_status" /></template>
        </el-table-column>
        <el-table-column prop="region_check_status" label="地区" width="90">
          <template #default="{ row }"><StatusTag :value="row.region_check_status" /></template>
        </el-table-column>
        <el-table-column prop="evidence_id" label="证据编号" min-width="170" show-overflow-tooltip />
      </el-table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Filter } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import { generateCandidates } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const loading = ref(false)
const hardRegion = ref(false)
const pool = computed(() => store.candidatePool)

async function run() {
  loading.value = true
  try {
    store.candidatePool = await generateCandidates(store.profile as any, hardRegion.value)
    ElMessage.success('候选池已更新')
  } catch (error: any) {
    store.lastError = error.message
    ElMessage.error('请求失败，请确认本地后端服务正常')
  } finally {
    loading.value = false
  }
}
</script>
