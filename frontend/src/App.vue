<template>
  <el-container class="layout">
    <el-aside class="side" width="238px">
      <div class="brand">
        <div class="brand-mark">SD</div>
        <div>
          <div class="brand-title">山东高考知识库</div>
          <div class="brand-subtitle">v3.9</div>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="nav">
        <el-menu-item index="/dashboard"><el-icon><DataAnalysis /></el-icon><span>Dashboard</span></el-menu-item>
        <el-menu-item index="/profile"><el-icon><User /></el-icon><span>Student Profile</span></el-menu-item>
        <el-menu-item index="/query"><el-icon><Search /></el-icon><span>Index Query</span></el-menu-item>
        <el-menu-item index="/candidates"><el-icon><Filter /></el-icon><span>Candidate Pool</span></el-menu-item>
        <el-menu-item index="/generate"><el-icon><Operation /></el-icon><span>Plan Generator</span></el-menu-item>
        <el-menu-item index="/review"><el-icon><TrendCharts /></el-icon><span>Plan Review</span></el-menu-item>
        <el-menu-item index="/reports"><el-icon><FolderOpened /></el-icon><span>Reports</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <div class="topbar-title">{{ routeTitle }}</div>
        <div class="topbar-actions">
          <el-tag effect="plain">local</el-tag>
          <el-tag :type="store.planJob?.status === 'failed' ? 'danger' : 'info'" effect="plain">
            {{ store.planJob?.status || 'idle' }}
          </el-tag>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataAnalysis, Filter, FolderOpened, Operation, Search, TrendCharts, User } from '@element-plus/icons-vue'
import { useAppStore } from './stores/app'

const route = useRoute()
const store = useAppStore()
const routeTitle = computed(() => String(route.meta.title || 'Dashboard'))
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

.side {
  background: #ffffff;
  border-right: 1px solid #e4e7ed;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 72px;
  padding: 0 18px;
  border-bottom: 1px solid #edf0f5;
}

.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #1f5fbf;
  color: #fff;
  font-weight: 800;
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
}

.brand-subtitle {
  margin-top: 2px;
  color: #7a8494;
  font-size: 12px;
}

.nav {
  border-right: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}

.topbar-title {
  font-weight: 700;
}

.topbar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.main {
  padding: 22px;
}
</style>
