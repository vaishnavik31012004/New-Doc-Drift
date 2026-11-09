import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: API_BASE_URL })

export const connectRepo = (owner, name, github_token) =>
  api.post('/api/repos', { owner, name, github_token: github_token || null }).then(r => r.data)

export const listRepos = () => api.get('/api/repos').then(r => r.data)

export const deleteRepo = (id) => api.delete(`/api/repos/${id}`).then(r => r.data)

export const listCommits = (repoId) =>
  api.get(`/api/repos/${repoId}/commits`).then(r => r.data)

export const createScan = (repository_id, commit_sha) =>
  api.post('/api/scans', { repository_id, commit_sha }).then(r => r.data)

export const listScans = (repositoryId) =>
  api.get('/api/scans', { params: repositoryId ? { repository_id: repositoryId } : {} }).then(r => r.data)

export const getScan = (scanId) => api.get(`/api/scans/${scanId}`).then(r => r.data)

export const createPR = (scanId, finding_ids) =>
  api.post(`/api/scans/${scanId}/create-pr`, { finding_ids }).then(r => r.data)

export const scanSocketUrl = (scanId) => {
  const wsBase = API_BASE_URL.replace('http', 'ws')
  return `${wsBase}/ws/scans/${scanId}`
}
