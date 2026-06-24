import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import StudentProfile from './views/StudentProfile.vue'
import IndexQuery from './views/IndexQuery.vue'
import CandidatePool from './views/CandidatePool.vue'
import PlanGenerator from './views/PlanGenerator.vue'
import PlanReview from './views/PlanReview.vue'
import Reports from './views/Reports.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard, meta: { title: '数据看板' } },
    { path: '/profile', component: StudentProfile, meta: { title: '学生画像' } },
    { path: '/query', component: IndexQuery, meta: { title: '证据查询' } },
    { path: '/candidates', component: CandidatePool, meta: { title: '候选池' } },
    { path: '/generate', component: PlanGenerator, meta: { title: '方案生成' } },
    { path: '/review', component: PlanReview, meta: { title: '方案复核' } },
    { path: '/reports', component: Reports, meta: { title: '报告下载' } }
  ]
})

export default router
