import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}

export async function getIndexSummary() {
  const { data } = await api.get('/indexes/summary')
  return data
}

export async function getAuditStatus() {
  const { data } = await api.get('/audit/status')
  return data
}

export async function checkSubject(payload: Record<string, unknown>) {
  const { data } = await api.post('/check/subject', payload)
  return data
}

export async function checkRegion(payload: Record<string, unknown>) {
  const { data } = await api.post('/check/region', payload)
  return data
}

export async function searchSchools(query: string, limit = 20) {
  const { data } = await api.post('/master/search-schools', { query, limit })
  return data
}

export async function searchMajors(query: string, limit = 20) {
  const { data } = await api.post('/master/search-majors', { query, limit })
  return data
}

export async function searchPrograms(payload: Record<string, unknown>) {
  const { data } = await api.post('/master/search-programs', payload)
  return data
}

export async function generateCandidates(profile: Record<string, unknown>, hardRegion = false) {
  const { data } = await api.post('/candidates/generate', { profile, hard_region: hardRegion })
  return data
}

export async function generatePlan(payload: Record<string, unknown>) {
  const { data } = await api.post('/plans/generate', payload)
  return data
}

export function fileUrl(fileId: string) {
  return `/api/files/${fileId}`
}
