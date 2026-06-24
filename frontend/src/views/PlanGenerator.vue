<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Plan Generator</h1>
        <p class="page-subtitle">96 志愿方案链</p>
      </div>
      <el-button type="primary" :icon="Operation" :loading="loading" @click="run">生成方案</el-button>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h2 class="panel-title">Inputs</h2>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="姓名">{{ store.profile.name }}</el-descriptions-item>
          <el-descriptions-item label="年份">{{ store.profile.year }}</el-descriptions-item>
          <el-descriptions-item label="分数">{{ store.profile.score }}</el-descriptions-item>
          <el-descriptions-item label="选科">{{ store.profile.subjects.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="地区">{{ store.profile.regions.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ store.profile.major_preferences.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="风险档">{{ store.profile.risk_profile }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div class="panel">
        <h2 class="panel-title">Job</h2>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="状态"><StatusTag :value="job?.status" /></el-descriptions-item>
          <el-descriptions-item label="硬闸门"><StatusTag :value="job?.result?.hard_gate_passed" /></el-descriptions-item>
          <el-descriptions-item label="模拟"><StatusTag :value="job?.result?.simulation" /></el-descriptions-item>
          <el-descriptions-item label="输出目录">{{ job?.result?.out_dir || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-alert v-if="job?.status === 'failed'" :title="job.reason_code" :description="job.error" type="error" show-icon />
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
      ElMessage.warning(store.planJob.reason_code || '方案未通过')
    }
  } catch (error: any) {
    store.lastError = error.message
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}
</script>
