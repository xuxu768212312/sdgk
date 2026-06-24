<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Student Profile</h1>
        <p class="page-subtitle">画像输入</p>
      </div>
      <el-button type="primary" :icon="Check" @click="saved = true">保存</el-button>
    </div>

    <div class="panel">
      <el-form :model="store.profile" label-width="110px">
        <div class="grid-2">
          <el-form-item label="姓名"><el-input v-model="store.profile.name" /></el-form-item>
          <el-form-item label="性别"><el-input v-model="store.profile.gender" /></el-form-item>
          <el-form-item label="年份"><el-input-number v-model="store.profile.year" :min="2025" :max="2030" /></el-form-item>
          <el-form-item label="批次"><el-input v-model="store.profile.batch" /></el-form-item>
          <el-form-item label="分数"><el-input-number v-model="store.profile.score" :min="0" :max="750" /></el-form-item>
          <el-form-item label="位次"><el-input-number v-model="store.profile.rank" :min="1" :max="800000" /></el-form-item>
          <el-form-item label="层次">
            <el-segmented v-model="store.profile.level" :options="['本科', '专科']" />
          </el-form-item>
          <el-form-item label="风险档">
            <el-select v-model="store.profile.risk_profile">
              <el-option label="保守" value="conservative" />
              <el-option label="标准" value="standard" />
              <el-option label="积极" value="aggressive" />
              <el-option label="机会型" value="opportunistic" />
            </el-select>
          </el-form-item>
          <el-form-item label="选科">
            <el-select v-model="store.profile.subjects" multiple>
              <el-option v-for="subject in subjects" :key="subject" :label="subject" :value="subject" />
            </el-select>
          </el-form-item>
          <el-form-item label="地区偏好">
            <el-select v-model="store.profile.regions" multiple filterable allow-create>
              <el-option v-for="region in regions" :key="region" :label="region" :value="region" />
            </el-select>
          </el-form-item>
          <el-form-item label="专业偏好" class="wide">
            <el-select v-model="store.profile.major_preferences" multiple filterable allow-create>
              <el-option v-for="major in majors" :key="major" :label="major" :value="major" />
            </el-select>
          </el-form-item>
          <el-form-item label="身体情况" class="wide"><el-input v-model="store.profile.health" /></el-form-item>
        </div>
      </el-form>
    </div>
    <el-alert v-if="saved" title="已保存到当前工作台状态" type="success" show-icon />
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Check } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const saved = ref(false)
const subjects = ['物理', '化学', '生物', '思想政治', '历史', '地理']
const regions = ['山东', '苏州', '青岛', '济南', '烟台', '江苏']
const majors = ['师范', '法学', '英语', '金融', '生物工程']
</script>

<style scoped>
.wide {
  grid-column: 1 / -1;
}
</style>
