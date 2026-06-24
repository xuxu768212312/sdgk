<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Index Query</h1>
        <p class="page-subtitle">选科、地区、院校、专业</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h2 class="panel-title">Subject</h2>
        <el-form label-width="96px">
          <el-form-item label="选科"><el-select v-model="subjectForm.subjects" multiple><el-option v-for="s in subjects" :key="s" :label="s" :value="s" /></el-select></el-form-item>
          <el-form-item label="院校代码"><el-input v-model="subjectForm.school_code" /></el-form-item>
          <el-form-item label="专业代码"><el-input v-model="subjectForm.major_code" /></el-form-item>
          <el-form-item label="院校名称"><el-input v-model="subjectForm.school_name" /></el-form-item>
          <el-form-item label="专业名称"><el-input v-model="subjectForm.major_name" /></el-form-item>
          <el-button type="primary" :icon="Search" @click="runSubject">查询</el-button>
        </el-form>
        <el-divider />
        <StatusTag :value="subjectResult?.status" />
        <pre class="json">{{ subjectResult }}</pre>
      </div>

      <div class="panel">
        <h2 class="panel-title">Region</h2>
        <el-form label-width="96px">
          <el-form-item label="地区"><el-select v-model="regionForm.regions" multiple filterable allow-create><el-option label="山东" value="山东" /><el-option label="苏州" value="苏州" /></el-select></el-form-item>
          <el-form-item label="院校名称"><el-input v-model="regionForm.school_name" /></el-form-item>
          <el-button type="primary" :icon="Location" @click="runRegion">查询</el-button>
        </el-form>
        <el-divider />
        <StatusTag :value="regionResult?.status" />
        <pre class="json">{{ regionResult }}</pre>
      </div>
    </div>

    <div class="panel">
      <h2 class="panel-title">Master Search</h2>
      <div class="toolbar">
        <el-input v-model="searchText" placeholder="院校或专业" clearable />
        <el-button :icon="Search" @click="runSearch">搜索</el-button>
      </div>
      <el-table :data="schoolRows" height="240">
        <el-table-column prop="school_name" label="院校" min-width="180" />
        <el-table-column prop="province" label="省份" width="90" />
        <el-table-column prop="city" label="城市" width="90" />
        <el-table-column prop="school_level_tag" label="层次" width="120" />
      </el-table>
      <el-table :data="majorRows" height="240">
        <el-table-column prop="major_name" label="专业" min-width="240" />
        <el-table-column prop="major_family" label="标签" width="120" />
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

<style scoped>
.json {
  max-height: 240px;
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: #f6f7f9;
  font-size: 12px;
}
</style>
