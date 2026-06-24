<template>
  <el-tag :type="tagType" effect="light" round>{{ displayValue }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value?: string | boolean }>()

const labelMap: Record<string, string> = {
  PASS: '通过',
  MATCH: '匹配',
  TRUE: '通过',
  OK: '正常',
  BLOCK: '阻断',
  FALSE: '未通过',
  FAILED: '失败',
  REVIEW: '待复核',
  NO_MATCH: '不匹配',
  UNKNOWN: '未知',
  IDLE: '待命',
  QUEUED: '排队中',
  RUNNING: '运行中',
  SUCCEEDED: '已完成',
  AVAILABLE: '可用'
}

const displayValue = computed(() => {
  const raw = String(props.value ?? '').trim()
  if (!raw) return '未知'
  return labelMap[raw.toUpperCase()] || raw
})

const tagType = computed(() => {
  const value = String(props.value ?? '').toUpperCase()
  if (value === 'PASS' || value === 'MATCH' || value === 'TRUE' || value === 'OK' || value === 'SUCCEEDED') return 'success'
  if (value === 'BLOCK' || value === 'FALSE' || value === 'FAILED') return 'danger'
  if (value === 'REVIEW' || value === 'NO_MATCH' || value === 'UNKNOWN' || value === '') return 'warning'
  return 'info'
})
</script>
