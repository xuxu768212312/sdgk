import { defineStore } from 'pinia'

export type StudentProfile = {
  name: string
  gender: string
  health: string
  year: number
  level: string
  batch: string
  score: number
  rank?: number | null
  subjects: string[]
  regions: string[]
  major_preferences: string[]
  risk_profile: 'conservative' | 'standard' | 'aggressive' | 'opportunistic'
}

export const useAppStore = defineStore('app', {
  state: () => ({
    profile: {
      name: '王二哈',
      gender: '女',
      health: '身体正常',
      year: 2026,
      level: '本科',
      batch: '普通类常规批',
      score: 495,
      rank: null,
      subjects: ['历史', '生物', '思想政治'],
      regions: ['山东', '苏州'],
      major_preferences: ['师范', '法学', '英语', '金融', '生物工程'],
      risk_profile: 'opportunistic'
    } as StudentProfile,
    candidatePool: null as any,
    planJob: null as any,
    lastError: ''
  }),
  getters: {
    finalAudit(state) {
      return state.planJob?.result?.hard_gate_passed ?? false
    },
    fileIds(state) {
      return state.planJob?.file_ids ?? {}
    }
  }
})
