<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">报告下载</h1>
        <p class="page-subtitle">志愿表、详细报告、审计文件</p>
      </div>
      <el-button type="success" :disabled="!formalReady" :icon="Download">正式导出</el-button>
    </div>

    <el-alert
      v-if="job && !formalReady"
      title="硬闸门未通过"
      type="warning"
      show-icon
    />
    <el-alert v-if="!job" title="暂无报告" type="info" show-icon />

    <div v-if="job" class="panel">
      <h2 class="panel-title">输出文件</h2>
      <el-table :data="files" height="420">
        <el-table-column prop="name" label="文件" min-width="180" />
        <el-table-column prop="path" label="路径" min-width="360" show-overflow-tooltip />
        <el-table-column label="下载" width="120">
          <template #default="{ row }">
            <el-button :icon="Download" tag="a" :href="row.url" target="_blank">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { fileUrl } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const job = computed(() => store.planJob)
const formalReady = computed(() => Boolean(job.value?.result?.hard_gate_passed))
const fileLabels: Record<string, string> = {
  excel: '志愿表',
  markdown: '详细报告',
  candidate_pool: '候选池',
  strategy_result: '策略结果',
  subject_audit: '选科审核',
  region_audit: '地区审核',
  final_audit: '最终审计',
  plan_meta: '方案元数据'
}
const files = computed(() => {
  const ids = job.value?.file_ids || {}
  const outputs = job.value?.outputs || {}
  return Object.keys(ids).map((name) => ({
    name: fileLabels[name] || '输出文件',
    path: outputs[name],
    url: fileUrl(ids[name])
  }))
})
</script>
