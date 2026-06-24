<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">证据查询</h1>
        <p class="page-subtitle">单条闸门、招生单元、院校库、专业库、代码复核</p>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="query-tabs">
      <el-tab-pane label="单条闸门" name="gates">
        <div class="grid-2">
          <div class="panel">
            <h2 class="panel-title">选科查询</h2>
            <el-form label-width="96px">
              <el-form-item label="选科">
                <el-select v-model="subjectForm.subjects" multiple>
                  <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
                </el-select>
              </el-form-item>
              <el-form-item label="院校代码"><el-input v-model="subjectForm.school_code" clearable /></el-form-item>
              <el-form-item label="专业代码"><el-input v-model="subjectForm.major_code" clearable /></el-form-item>
              <el-form-item label="院校名称"><el-input v-model="subjectForm.school_name" clearable /></el-form-item>
              <el-form-item label="专业名称"><el-input v-model="subjectForm.major_name" clearable /></el-form-item>
              <el-button type="primary" :icon="Search" :loading="subjectLoading" @click="runSubject">查询</el-button>
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
              <el-form-item label="地区">
                <el-select v-model="regionForm.regions" multiple filterable allow-create>
                  <el-option label="山东" value="山东" />
                  <el-option label="苏州" value="苏州" />
                </el-select>
              </el-form-item>
              <el-form-item label="院校名称"><el-input v-model="regionForm.school_name" clearable /></el-form-item>
              <el-button type="primary" :icon="Location" :loading="regionLoading" @click="runRegion">查询</el-button>
            </el-form>
            <el-divider />
            <el-descriptions v-if="regionResult" :column="1" border>
              <el-descriptions-item label="状态"><StatusTag :value="regionResult.status" /></el-descriptions-item>
              <el-descriptions-item label="地区结论">{{ regionReasonText(regionResult.reason_code) }}</el-descriptions-item>
              <el-descriptions-item label="匹配方式">{{ matchText(regionResult.match_type) }}</el-descriptions-item>
              <el-descriptions-item label="省份">{{ regionResult.province || '-' }}</el-descriptions-item>
              <el-descriptions-item label="城市">{{ regionResult.city || '-' }}</el-descriptions-item>
              <el-descriptions-item label="证据编号">{{ regionResult.evidence_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="来源文件">{{ regionResult.source_file || '-' }}</el-descriptions-item>
            </el-descriptions>
            <el-empty v-else description="暂无查询结果" :image-size="72" />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="招生单元" name="programs">
        <div class="panel">
          <h2 class="panel-title">招生单元检索</h2>
          <el-form :inline="true" class="query-form">
            <el-form-item label="关键词"><el-input v-model="programForm.query" clearable /></el-form-item>
            <el-form-item label="院校"><el-input v-model="programForm.school_name" clearable /></el-form-item>
            <el-form-item label="专业"><el-input v-model="programForm.major_name" clearable /></el-form-item>
            <el-form-item label="院校代码"><el-input v-model="programForm.school_code" clearable /></el-form-item>
            <el-form-item label="专业代码"><el-input v-model="programForm.major_code" clearable /></el-form-item>
            <el-form-item label="年份"><el-input-number v-model="programForm.year" :min="2020" :max="2027" controls-position="right" /></el-form-item>
            <el-button type="primary" :icon="Search" :loading="programLoading" @click="runProgramSearch">搜索</el-button>
          </el-form>
          <el-table :data="programRows" height="500" border>
            <el-table-column prop="year" label="年份" width="80" />
            <el-table-column prop="school_code" label="院校代码" width="100" />
            <el-table-column prop="school_name" label="院校" min-width="170" />
            <el-table-column prop="major_code" label="专业代码" width="100" />
            <el-table-column prop="major_name" label="专业" min-width="260" show-overflow-tooltip />
            <el-table-column prop="min_rank" label="最低位次" width="110" sortable />
            <el-table-column prop="plan_count" label="计划数" width="90" />
            <el-table-column prop="major_family" label="专业族" width="110" />
            <el-table-column prop="province" label="省份" width="90" />
            <el-table-column prop="city" label="城市" width="90" />
            <el-table-column prop="program_id" label="招生单元编号" min-width="170" show-overflow-tooltip />
            <el-table-column prop="evidence_id" label="证据编号" min-width="170" show-overflow-tooltip />
            <el-table-column prop="source_file" label="来源文件" min-width="220" show-overflow-tooltip />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="院校库" name="schools">
        <div class="panel">
          <h2 class="panel-title">院校检索</h2>
          <div class="toolbar">
            <el-input v-model="schoolSearchText" placeholder="院校名称" clearable />
            <el-button type="primary" :icon="Search" :loading="schoolLoading" @click="runSchoolSearch">搜索</el-button>
          </div>
          <el-table :data="schoolRows" height="500" border>
            <el-table-column prop="school_name" label="院校" min-width="180" />
            <el-table-column prop="province" label="省份" width="90" />
            <el-table-column prop="city" label="城市" width="90" />
            <el-table-column prop="city_status" label="城市状态" width="110" />
            <el-table-column prop="school_level_tag" label="层次" width="120" />
            <el-table-column prop="program_count" label="招生单元" width="100" />
            <el-table-column prop="subject_school_code_count" label="选科代码" width="100" />
            <el-table-column prop="admission_school_code_count" label="投档代码" width="100" />
            <el-table-column prop="code_status" label="代码状态" width="110">
              <template #default="{ row }"><StatusTag :value="row.code_status" /></template>
            </el-table-column>
            <el-table-column prop="evidence_id" label="证据编号" min-width="170" show-overflow-tooltip />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="专业库" name="majors">
        <div class="panel">
          <h2 class="panel-title">专业检索</h2>
          <div class="toolbar">
            <el-input v-model="majorSearchText" placeholder="专业名称" clearable />
            <el-button type="primary" :icon="Search" :loading="majorLoading" @click="runMajorSearch">搜索</el-button>
          </div>
          <el-table :data="majorRows" height="500" border>
            <el-table-column prop="major_name" label="专业" min-width="240" />
            <el-table-column prop="major_family" label="专业族" width="120" />
            <el-table-column label="偏好标签" min-width="150" show-overflow-tooltip>
              <template #default="{ row }">{{ tagText(row.preference_tags) }}</template>
            </el-table-column>
            <el-table-column label="代码样本" min-width="150" show-overflow-tooltip>
              <template #default="{ row }">{{ codeText(row.major_code_samples) }}</template>
            </el-table-column>
            <el-table-column prop="major_code_count" label="代码数" width="90" />
            <el-table-column prop="program_count" label="招生单元" width="100" />
            <el-table-column prop="classification_status" label="状态" width="110">
              <template #default="{ row }"><StatusTag :value="row.classification_status" /></template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="代码复核" name="codes">
        <div class="grid-2">
          <div class="panel">
            <h2 class="panel-title">院校代码</h2>
            <el-form :inline="true" class="query-form">
              <el-form-item label="代码"><el-input v-model="schoolCodeForm.code" clearable /></el-form-item>
              <el-button type="primary" :icon="Search" :loading="schoolAliasLoading" @click="runSchoolCodeSearch">搜索</el-button>
            </el-form>
            <el-table :data="schoolAliasRows" height="320" border>
              <el-table-column prop="school_code" label="院校代码" width="100" />
              <el-table-column prop="code_source" label="代码来源" width="100" />
              <el-table-column prop="school_name" label="院校" min-width="180" />
              <el-table-column prop="province" label="省份" width="90" />
              <el-table-column prop="city" label="城市" width="90" />
              <el-table-column prop="ambiguity_status" label="状态" width="110">
                <template #default="{ row }"><StatusTag :value="row.ambiguity_status" /></template>
              </el-table-column>
            </el-table>
          </div>

          <div class="panel">
            <h2 class="panel-title">专业代码</h2>
            <el-form :inline="true" class="query-form">
              <el-form-item label="代码"><el-input v-model="majorCodeForm.code" clearable /></el-form-item>
              <el-button type="primary" :icon="Search" :loading="majorAliasLoading" @click="runMajorCodeSearch">搜索</el-button>
            </el-form>
            <el-table :data="majorAliasRows" height="320" border>
              <el-table-column prop="major_code" label="专业代码" width="100" />
              <el-table-column prop="code_source" label="代码来源" width="100" />
              <el-table-column prop="major_name" label="专业" min-width="220" show-overflow-tooltip />
              <el-table-column prop="major_family" label="专业族" width="120" />
              <el-table-column prop="ambiguity_status" label="状态" width="110">
                <template #default="{ row }"><StatusTag :value="row.ambiguity_status" /></template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Location, Search } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import {
  checkRegion,
  checkSubject,
  searchMajorCodeAliases,
  searchMajors,
  searchPrograms,
  searchSchoolCodeAliases,
  searchSchools
} from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const activeTab = ref('gates')
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
const programForm = reactive({
  query: '青岛大学',
  school_name: '',
  major_name: '法学',
  school_code: '',
  major_code: '',
  year: undefined as number | undefined,
  limit: 80
})
const schoolCodeForm = reactive({ code: 'B065', limit: 50 })
const majorCodeForm = reactive({ code: '01', limit: 50 })

const subjectResult = ref<any>(null)
const regionResult = ref<any>(null)
const schoolRows = ref<any[]>([])
const majorRows = ref<any[]>([])
const programRows = ref<any[]>([])
const schoolAliasRows = ref<any[]>([])
const majorAliasRows = ref<any[]>([])
const schoolSearchText = ref('青岛大学')
const majorSearchText = ref('法学')
const subjectLoading = ref(false)
const regionLoading = ref(false)
const programLoading = ref(false)
const schoolLoading = ref(false)
const majorLoading = ref(false)
const schoolAliasLoading = ref(false)
const majorAliasLoading = ref(false)

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

function showError() {
  ElMessage.error('查询失败，请确认本地后端服务正常')
}

async function runSubject() {
  subjectLoading.value = true
  try {
    subjectResult.value = await checkSubject(subjectForm)
  } catch {
    showError()
  } finally {
    subjectLoading.value = false
  }
}

async function runRegion() {
  regionLoading.value = true
  try {
    regionResult.value = await checkRegion(regionForm)
  } catch {
    showError()
  } finally {
    regionLoading.value = false
  }
}

async function runProgramSearch() {
  programLoading.value = true
  try {
    programRows.value = await searchPrograms(programForm)
  } catch {
    showError()
  } finally {
    programLoading.value = false
  }
}

async function runSchoolSearch() {
  schoolLoading.value = true
  try {
    schoolRows.value = await searchSchools(schoolSearchText.value, 80)
  } catch {
    showError()
  } finally {
    schoolLoading.value = false
  }
}

async function runMajorSearch() {
  majorLoading.value = true
  try {
    majorRows.value = await searchMajors(majorSearchText.value, 80)
  } catch {
    showError()
  } finally {
    majorLoading.value = false
  }
}

async function runSchoolCodeSearch() {
  schoolAliasLoading.value = true
  try {
    schoolAliasRows.value = await searchSchoolCodeAliases(schoolCodeForm)
  } catch {
    showError()
  } finally {
    schoolAliasLoading.value = false
  }
}

async function runMajorCodeSearch() {
  majorAliasLoading.value = true
  try {
    majorAliasRows.value = await searchMajorCodeAliases(majorCodeForm)
  } catch {
    showError()
  } finally {
    majorAliasLoading.value = false
  }
}
</script>

<style scoped>
.query-tabs {
  margin-top: 2px;
}

.query-tabs :deep(.el-tabs__content) {
  overflow: visible;
}

.query-form {
  margin-bottom: 12px;
}

.query-form :deep(.el-form-item) {
  margin-right: 12px;
  margin-bottom: 10px;
}

.query-form :deep(.el-input) {
  width: 180px;
}

.query-form :deep(.el-input-number) {
  width: 132px;
}

@media (max-width: 900px) {
  .query-form :deep(.el-form-item) {
    display: block;
    margin-right: 0;
  }

  .query-form :deep(.el-input),
  .query-form :deep(.el-input-number) {
    width: 100%;
  }
}
</style>
