<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">索引查询</h1>
        <p class="page-subtitle">选科、地区、院校、专业</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h2 class="panel-title">选科查询</h2>
        <el-form label-width="96px">
          <el-form-item label="选科"><el-select v-model="subjectForm.subjects" multiple><el-option v-for="s in subjects" :key="s" :label="s" :value="s" /></el-select></el-form-item>
          <el-form-item label="院校代码"><el-input v-model="subjectForm.school_code" /></el-form-item>
          <el-form-item label="专业代码"><el-input v-model="subjectForm.major_code" /></el-form-item>
          <el-form-item label="院校名称"><el-input v-model="subjectForm.school_name" /></el-form-item>
          <el-form-item label="专业名称"><el-input v-model="subjectForm.major_name" /></el-form-item>
          <el-button type="primary" :icon="Search" @click="runSubject">查询</el-button>
        </el-form>
        <el-divider />
        <el-descriptions v-if="subjectResult" :column="1" border>
          <el-descriptions-item label="状态"><StatusTag :value="subjectResult.status" /></el-descriptions-item>
          <el-descriptions-item label="是否可报">{{ eligibleText(subjectResult.eligible) }}</el-descriptions-item>
          <el-descriptions-item label="原因">{{ reasonText(subjectResult.reason_code) }}</el-descriptions-item>
          <el-descriptions-item label="匹配方式">{{ matchText(subjectResult.match_type) }}</el-descriptions-item>
          <el-descriptions-item label="证据编号">{{ subjectResult.evidence_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="来源文件">{{ subjectResult.source_file || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无查询结果" :image-size="72" />
      </div>

      <div class="panel">
        <h2 class="panel-title">地区查询</h2>
        <el-form label-width="96px">
          <el-form-item label="地区"><el-select v-model="regionForm.regions" multiple filterable allow-create><el-option label="山东" value="山东" /><el-option label="苏州" value="苏州" /></el-select></el-form-item>
          <el-form-item label="院校名称"><el-input v-model="regionForm.school_name" /></el-form-item>
          <el-button type="primary" :icon="Location" @click="runRegion">查询</el-button>
        </el-form>
        <el-divider />
        <el-descriptions v-if="regionResult" :column="1" border>
          <el-descriptions-item label="状态"><StatusTag :value="regionResult.status" /></el-descriptions-item>
          <el-descriptions-item label="地区结论">{{ regionReasonText(regionResult.reason_code) }}</el-descriptions-item>
          <el-descriptions-item label="匹配方式">{{ matchText(regionResult.match_type) }}</el-descriptions-item>
          <el-descriptions-item label="省份">{{ regionResult.province || '-' }}</el-descriptions-item>
          <el-descriptions-item label="城市">{{ regionResult.city || '-' }}</el-descriptions-item>
          <el-descriptions-item label="证据编号">{{ regionResult.evidence_id || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无查询结果" :image-size="72" />
      </div>
    </div>

    <div class="panel">
      <h2 class="panel-title">主索引搜索</h2>
      <div class="toolbar">
        <el-input v-model="searchText" placeholder="院校或专业" clearable />
        <el-button :icon="Search" @click="runSearch">搜索</el-button>
      </div>
      <el-table :data="schoolRows" height="240">
        <el-table-column prop="school_name" label="院校" min-width="180" />
        <el-table-column prop="province" label="省份" width="90" />
        <el-table-column prop="city" label="城市" width="90" />
        <el-table-column prop="school_level_tag" label="层次" width="120" />
        <el-table-column prop="program_count" label="招生单元" width="100" />
        <el-table-column prop="subject_school_code_count" label="选科代码" width="100" />
        <el-table-column prop="admission_school_code_count" label="投档代码" width="100" />
        <el-table-column prop="code_status" label="代码状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.code_status" /></template>
        </el-table-column>
      </el-table>
      <el-table :data="majorRows" height="240">
        <el-table-column prop="major_name" label="专业" min-width="240" />
        <el-table-column prop="major_family" label="专业族" width="120" />
        <el-table-column label="偏好标签" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ tagText(row.preference_tags) }}</template>
        </el-table-column>
        <el-table-column label="代码样本" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ codeText(row.major_code_samples) }}</template>
        </el-table-column>
        <el-table-column prop="major_code_count" label="代码数" width="90" />
        <el-table-column prop="program_count" label="招生单元" width="100" />
        <el-table-column prop="classification_status" label="状态" width="110">
          <template #default="{ row }"><StatusTag :value="row.classification_status" /></template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Location, Search } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import { checkRegion, checkSubject, searchMajors, searchSchools } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const subjects = ['物理', '化学', '生物', '思想政治', '历史', '地理']
const subjectForm = reactive({
  year: 2026,
  level: '本科',
  subjects: [...store.profile.subjects],
  school_code: '',
  major_code: '',
  school_name: '青岛大学',
  major_name: ''
})
const regionForm = reactive({ regions: [...store.profile.regions], school_name: '青岛大学' })
const subjectResult = ref<any>(null)
const regionResult = ref<any>(null)
const searchText = ref('青岛大学')
const schoolRows = ref<any[]>([])
const majorRows = ref<any[]>([])
const reasonLabels: Record<string, string> = {
  ELIGIBLE: '选科满足要求',
  INELIGIBLE: '选科不满足要求',
  NO_REQUIREMENT: '不限选科',
  MISSING_FIELD: '字段缺失',
  YEAR_REVIEW: '年份无法自动判定',
  NOT_FOUND: '索引未命中',
  AMBIGUOUS: '存在多条匹配，需人工复核',
  SUBJECT_MISMATCH: '选科不符合要求',
  SUBJECT_MATCH: '选科符合要求'
}
const regionReasonLabels: Record<string, string> = {
  PROVINCE_MATCH: '省份匹配',
  CITY_MATCH: '城市匹配',
  NO_MATCH: '地区不匹配',
  CITY_REVIEW: '城市或校区需人工复核',
  NOT_FOUND: '地区索引未命中',
  AMBIGUOUS: '院校名称不唯一，需人工复核'
}
const matchLabels: Record<string, string> = {
  exact_code: '代码精确匹配',
  unique_name: '名称唯一匹配',
  province_exact: '省份精确匹配',
  city_exact: '城市精确匹配',
  reviewed_override: '人工复核映射',
  none: '未匹配'
}

function eligibleText(value?: boolean) {
  if (value === true) return '可报'
  if (value === false) return '不可报'
  return '待复核'
}

function reasonText(value?: string) {
  if (!value) return '无'
  return reasonLabels[value] || '需人工复核'
}

function regionReasonText(value?: string) {
  if (!value) return '无'
  return regionReasonLabels[value] || '需人工复核'
}

function matchText(value?: string) {
  if (!value) return '无'
  return matchLabels[value] || '其他匹配'
}

function tagText(value?: string) {
  return value ? value.split('|').filter(Boolean).join('、') : '待复核'
}

function codeText(value?: string) {
  const codes = value ? value.split('|').filter(Boolean) : []
  if (!codes.length) return '无'
  return codes.slice(0, 5).join('、') + (codes.length > 5 ? ' 等' : '')
}

async function runSubject() {
  subjectResult.value = await checkSubject(subjectForm)
}

async function runRegion() {
  regionResult.value = await checkRegion(regionForm)
}

async function runSearch() {
  const [schools, majors] = await Promise.all([searchSchools(searchText.value), searchMajors(searchText.value)])
  schoolRows.value = schools
  majorRows.value = majors
}
</script>
