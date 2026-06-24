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
    { path: '/dashboard', component: Dashboard, meta: { title: 'Dashboard' } },
    { path: '/profile', component: StudentProfile, meta: { title: 'Student Profile' } },
    { path: '/query', component: IndexQuery, meta: { title: 'Index Query' } },
    { path: '/candidates', component: CandidatePool, meta: { title: 'Candidate Pool' } },
    { path: '/generate', component: PlanGenerator, meta: { title: 'Plan Generator' } },
    { path: '/review', component: PlanReview, meta: { title: 'Plan Review' } },
    { path: '/reports', component: Reports, meta: { title: 'Reports' } }
  ]
})

export default router
