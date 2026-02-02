import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

// Add request interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        error.message = 'Request timeout. Please try again.'
      } else if (error.message === 'Network Error') {
        error.message = 'Unable to connect to server. Please check if the backend is running.'
      } else {
        error.message = 'Network error. Please check your connection and try again.'
      }
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Query (60s timeout - LLM + RAG can be slow, especially on cold start)
  query: async (data) => {
    const response = await client.post('/query', data, { timeout: 60000 })
    return response.data
  },

  queryWithFiles: async (query, files, options = {}) => {
    const formData = new FormData()
    formData.append('query', query)
    if (options.userId) formData.append('user_id', options.userId)
    if (options.difficultyLevel) formData.append('difficulty_level', options.difficultyLevel)
    if (options.systemFilter) formData.append('system_filter', options.systemFilter)
    if (options.clinicalOnly) formData.append('clinical_only', 'true')
    files.forEach(f => formData.append('files', f))
    const response = await client.post('/query/with-files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
    return response.data
  },

  // Teaching (60s timeout for LLM)
  teach: async (data) => {
    const response = await client.post('/teach', data, { timeout: 60000 })
    return response.data
  },

  // Quiz (90s timeout - generates multiple LLM questions)
  startQuiz: async (data) => {
    const response = await client.post('/quiz/start', data, { timeout: 90000 })
    return response.data
  },

  submitAnswer: async (data) => {
    const response = await client.post('/quiz/answer', data, { timeout: 30000 })
    return response.data
  },

  getFeedback: async (quizId, questionId, userId) => {
    const response = await client.get(`/quiz/feedback/${quizId}/${questionId}`, {
      params: { user_id: userId }
    })
    return response.data
  },

  // Upload
  uploadFile: async (file, source = 'uploaded_file') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source', source)
    const response = await client.post('/ingest/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Progress
  getProgress: async (userId) => {
    const response = await client.get('/user/progress', {
      params: { user_id: userId }
    })
    return response.data
  },

  // Study (longer timeout for LLM generation)
  generateFlashCards: async (data) => {
    const response = await client.post('/study/flash-cards', data, { timeout: 60000 })
    return response.data
  },

  evaluateFlashCardAnswer: async (data) => {
    const response = await client.post('/study/flash-cards/evaluate', data, { timeout: 30000 })
    return response.data
  },

  analyzeFlashCardSession: async (data) => {
    const response = await client.post('/study/flash-cards/analyze', data, { timeout: 45000 })
    return response.data
  },

  generateClinicalCase: async (data) => {
    const response = await client.post('/study/clinical-case', data, { timeout: 60000 })
    return response.data
  },

  startClinicalSession: async (data) => {
    const response = await client.post('/study/clinical-session/start', data, { timeout: 60000 })
    return response.data
  },

  interactClinicalSession: async (data) => {
    const response = await client.post('/study/clinical-session/interact', data, { timeout: 45000 })
    return response.data
  },

  generateStudyNotes: async (data) => {
    const response = await client.post('/study/notes', data, { timeout: 60000 })
    return response.data
  },

  // Health
  health: async () => {
    const response = await client.get('/health')
    return response.data
  },
}

export default api

