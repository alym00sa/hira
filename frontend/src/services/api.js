import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Chat API
export const chatAPI = {
  sendMessage: async (message, conversationId = null) => {
    const response = await api.post('/chat', {
      message,
      conversation_id: conversationId,
    })
    return response.data
  },

  getHistory: async (conversationId) => {
    const response = await api.get(`/chat/history/${conversationId}`)
    return response.data
  },
}

// Documents API
export const documentsAPI = {
  upload: async (file, onProgress = null) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(percentCompleted)
        }
      },
    })
    return response.data
  },

  list: async () => {
    const response = await api.get('/documents')
    return response.data
  },

  delete: async (documentId) => {
    const response = await api.delete(`/documents/${documentId}`)
    return response.data
  },

  getDocument: async (documentId) => {
    const response = await api.get(`/documents/${documentId}`)
    return response.data
  },
}

// Health API
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },
}

// Meetings API
export const meetingsAPI = {
  list: async (params = {}) => {
    const response = await api.get('/meetings', { params })
    return response.data
  },

  get: async (meetingId) => {
    const response = await api.get(`/meetings/${meetingId}`)
    return response.data
  },

  getByShareToken: async (shareToken) => {
    const response = await api.get(`/meetings/share/${shareToken}`)
    return response.data
  },

  create: async (meetingData) => {
    const response = await api.post('/meetings', meetingData)
    return response.data
  },

  update: async (meetingId, meetingData) => {
    const response = await api.patch(`/meetings/${meetingId}`, meetingData)
    return response.data
  },

  delete: async (meetingId) => {
    const response = await api.delete(`/meetings/${meetingId}`)
    return response.data
  },

  generateSummary: async (meetingId) => {
    const response = await api.post(`/meetings/${meetingId}/generate-summary`)
    return response.data
  },

  createShareLink: async (meetingId) => {
    const response = await api.post(`/meetings/${meetingId}/share`)
    return response.data
  },
}

// Bot API
export const botAPI = {
  start: async (botData) => {
    const response = await api.post('/bot/start', botData)
    return response
  },

  stop: async (botId) => {
    const response = await api.post(`/bot/${botId}/stop`)
    return response
  },

  getStatus: async (botId) => {
    const response = await api.get(`/bot/${botId}/status`)
    return response.data
  },
}

export default api
