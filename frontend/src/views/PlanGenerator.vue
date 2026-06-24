<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">方案生成</h1>
        <p class="page-subtitle">96 志愿方案链</p>
      </div>
      <el-button type="primary" :icon="Operation" :loading="loading" @click="run">生成方案</el-button>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h2 class="panel-title">输入画像</h2>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="姓名">{{ store.profile.name }}</el-descriptions-item>
          <el-descriptions-item label="年份">{{ store.profile.year }}</el-descriptions-item>
          <el-descriptions-item label="分数">{{ store.profile.score }}</el-descriptions-item>
          <el-descriptions-item label="选科">{{ store.profile.subjects.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="地区">{{ store.profile.regions.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ store.profile.major_preferences.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="风险档">{{ riskLabel(store.profile.risk_profile) }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div class="panel">
        <h2 class="panel-title">生成任务</h2>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="状态"><StatusTag :value="job?.status" /></el-descriptions-item>
          <el-descriptions-item label="硬闸门"><StatusTag :value="job?.result?.hard_gate_passed" /></el-descriptions-item>
          <el-descriptions-item label="模拟"><StatusTag :value="job?.result?.simulation" /></el-descriptions-item>
          <el-descriptions-item label="输出目录">{{ job?.result?.out_dir || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-alert
          v-if="job?.status === 'failed'"
          :title="reasonText(job.reason_code)"
          description="生成链路返回错误，已按失败关闭阻断交付。请查看终端或审计文件。"
          type="error"
          show-icon
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import { generatePlan } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const loading = ref(false)
const job = computed(() => store.planJob)
const riskLabels: Record<string, string> = {
  conservative: '保守',
  standard: '标准',
  aggressive: '积极',
  opportunistic: '机会型'
}
const reasonLabels: Record<string, string> = {
  STRATEGY_HARD_GATE_FAILED: '策略硬闸门未通过',
  VOLUNTEER_COUNT_NOT_96: '志愿数量不足 96',
  SUBJECT_NOT_PASS: '选科未全部通过',
  REGION_NOT_RESOLVED: '地区偏好未全部确认',
  MISSING_REQUIRED_FIELDS: '缺少必填字段',
  PATH_OUTSIDE_WORKSPACE: '路径超出工作区',
  PLAN_GENERATION_FAILED: '方案生成失败'
}

function riskLabel(value: string) {
  return riskLabels[value] || value
}

function reasonText(value?: string) {
  if (!value) return '任务失败'
  return reasonLabels[value] || '任务失败'
}

async function run() {
  loading.value = true
  try {
    store.planJob = await generatePlan({
      profile: store.profile,
      risk_profile: store.profile.risk_profile,
      hard_region: false,
      slots: 96
    })
    if (store.planJob.status === 'succeeded') {
      ElMessage.success('方案已生成')
    } else {
      ElMessage.warning(reasonText(store.planJob.reason_code) || '方案未通过')
    }
  } catch (error: any) {
    store.lastError = error.message
    ElMessage.error('请求失败，请确认本地后端服务正常')
  } finally {
    loading.value = false
  }
}
</script>
