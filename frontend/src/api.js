import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export const getSources = () => api.get('/sources').then(r => r.data)

export const getProperties = (params = {}) => api.get('/properties', { params }).then(r => r.data)

export const getEditions = (params = {}) => api.get('/editions', { params }).then(r => r.data)

export const getSuggestions = (params = {}) =>
  api.get('/suggestions', { params }).then(r => r.data)
export const createSuggestion = (payload) => api.post('/suggestions', payload).then(r => r.data)

export default api
