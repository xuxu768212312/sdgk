<template>
  <el-tag :type="tagType" effect="light" round>{{ value || 'UNKNOWN' }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value?: string | boolean }>()

const tagType = computed(() => {
  const value = String(props.value ?? '').toUpperCase()
  if (value === 'PASS' || value === 'MATCH' || value === 'TRUE' || value === 'OK') return 'success'
  if (value === 'BLOCK' || value === 'FALSE' || value === 'FAILED') return 'danger'
  if (value === 'REVIEW' || value === 'NO_MATCH' || value === 'UNKNOWN') return 'warning'
  return 'info'
})
</script>
