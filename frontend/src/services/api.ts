import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { AccessGroup, AdminUser, AiModel, ApiError, ChatQueryResponse, ChatSummary, HistoryMessage, KnowledgeBase, Message, PasswordResetRequest, PermissionOverride, ProviderName, ProviderStatus, TokenResponse, User } from '../types'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''
export const api = axios.create({ baseURL, withCredentials: true, headers: { 'Content-Type': 'application/json' } })
let accessToken: string | null = null
let refreshPromise: Promise<string | null> | null = null

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

export function setAccessToken(token: string | null) { accessToken = token }
export function getApiError(error: unknown): string {
  const apiError = error as AxiosError<ApiError>
  const response = apiError.response?.data
  if (response?.error?.message) return response.error.message
  if (typeof response?.detail === 'string') return response.detail
  if (response?.detail?.message) return response.detail.message
  if (response?.message) return response.message
  if (apiError.message) return apiError.message
  return 'Não foi possível concluir a operação.'
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = axios.post<TokenResponse>(`${baseURL}/api/auth/refresh`, undefined, { withCredentials: true })
      .then(({ data }) => { setAccessToken(data.access_token); return data.access_token })
      .catch(() => { setAccessToken(null); return null })
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

api.interceptors.response.use((response) => response, async (error: AxiosError) => {
  const config = error.config as RetriableConfig | undefined
  if (error.response?.status !== 401 || !config || config._retry || config.url?.includes('/auth/refresh')) throw error
  config._retry = true
  const token = await refreshAccessToken()
  if (!token) throw error
  config.headers.Authorization = `Bearer ${token}`
  return api(config)
})

export const authApi = {
  login: (payload: { email: string; password: string }) => api.post<TokenResponse>('/api/auth/login', payload).then((r) => r.data),
  refresh: () => refreshAccessToken(),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get<User>('/api/auth/me').then((r) => r.data),
  changePassword: (payload: { current_password: string; new_password: string }) => api.post<TokenResponse>('/api/auth/password', payload).then((r) => r.data),
  requestPasswordReset: (email: string) => api.post<{ message: string }>('/api/auth/password-reset-requests', { email }).then((r) => r.data),
}

export const chatsApi = {
  list: () => api.get<ChatSummary[]>('/api/chats').then((r) => r.data),
  create: () => api.post<ChatSummary>('/api/chats').then((r) => r.data),
  messages: (chatId: string) => api.get<Message[]>(`/api/chats/${chatId}/messages`).then((r) => r.data),
  rename: (chatId: string, title: string) => api.patch<ChatSummary>(`/api/chats/${chatId}`, { title }).then((r) => r.data),
  remove: (chatId: string) => api.delete(`/api/chats/${chatId}`),
}

export const adminApi = {
  users: () => api.get<AdminUser[]>('/api/admin/users').then((r) => r.data),
  createUser: (payload: { email: string; name: string; password: string }) => api.post<AdminUser>('/api/admin/users', payload).then((r) => r.data),
  updateUser: (userId: string, payload: { name?: string; password?: string; is_active?: boolean; is_blacklisted?: boolean }) => api.patch<AdminUser>(`/api/admin/users/${userId}`, payload).then((r) => r.data),
  passwordResetRequests: () => api.get<PasswordResetRequest[]>('/api/admin/password-reset-requests').then((r) => r.data),
  resetPassword: (requestId: string, password: string) => api.post(`/api/admin/password-reset-requests/${requestId}/reset`, { password }),
  models: () => api.get<AiModel[]>('/api/admin/models').then((r) => r.data),
  createAiModel: (payload: { provider: string; name: string; model_id: string }) => api.post<AiModel>('/api/admin/ai-models', payload).then((r) => r.data),
  updateAiModel: (id: string, payload: { provider?: string; name?: string; model_id?: string; is_active?: boolean }) => api.patch<AiModel>(`/api/admin/ai-models/${id}`, payload).then((r) => r.data),
  removeAiModel: (id: string) => api.delete(`/api/admin/ai-models/${id}`),
  knowledgeBases: () => api.get<KnowledgeBase[]>('/api/admin/knowledge-bases').then((r) => r.data),
  createKnowledgeBase: (payload: { name: string; store_id: string }) => api.post<KnowledgeBase>('/api/admin/knowledge-bases', payload).then((r) => r.data),
  updateKnowledgeBase: (id: string, payload: { name?: string; store_id?: string; is_active?: boolean; featured?: boolean }) => api.patch<KnowledgeBase>(`/api/admin/knowledge-bases/${id}`, payload).then((r) => r.data),
  removeKnowledgeBase: (id: string) => api.delete(`/api/admin/knowledge-bases/${id}`),
  groups: () => api.get<AccessGroup[]>('/api/admin/groups').then((r) => r.data),
  createGroup: (payload: { name: string }) => api.post<AccessGroup>('/api/admin/groups', payload).then((r) => r.data),
  updateGroup: (id: string, payload: { name: string }) => api.patch<AccessGroup>(`/api/admin/groups/${id}`, payload).then((r) => r.data),
  removeGroup: (id: string) => api.delete(`/api/admin/groups/${id}`),
  replaceGroupMembers: (id: string, userIds: string[]) => api.put<AccessGroup>(`/api/admin/groups/${id}/members`, { userIds }).then((r) => r.data),
  replaceGroupGrants: (id: string, payload: { knowledgeBaseIds: string[]; webSearch: boolean }) => api.put<AccessGroup>(`/api/admin/groups/${id}/grants`, payload).then((r) => r.data),
  permissionOverrides: (userId: string) => api.get<PermissionOverride[]>(`/api/admin/users/${userId}/permission-overrides`).then((r) => r.data),
  replacePermissionOverrides: (userId: string, overrides: PermissionOverride[]) => api.put<PermissionOverride[]>(`/api/admin/users/${userId}/permission-overrides`, { overrides: overrides.map(({ capability, knowledgeBaseId, allowed }) => ({ capability, ...(knowledgeBaseId ? { knowledgeBaseId } : {}), allowed })) }).then((r) => r.data),
  providers: () => api.get<ProviderStatus[]>('/api/admin/provider-keys').then((r) => r.data),
  saveProviderCredential: (provider: ProviderName, apiKey: string) => api.put<ProviderStatus>(`/api/admin/provider-keys/${provider}`, { apiKey }).then((r) => r.data),
  removeProviderCredential: (provider: ProviderName) => api.delete(`/api/admin/provider-keys/${provider}`),
  importProviderCredential: (provider: ProviderName) => api.post<ProviderStatus>(`/api/admin/provider-keys/${provider}/import-env`).then((r) => r.data),
  revertProviderToEnv: (provider: ProviderName) => api.post<ProviderStatus>(`/api/admin/provider-keys/${provider}/revert-to-env`).then((r) => r.data),
}

export const catalogsApi = {
  aiModels: () => api.get<AiModel[]>('/api/ai-models').then((r) => r.data),
  knowledgeBases: () => api.get<KnowledgeBase[]>('/api/knowledge-bases').then((r) => r.data),
}

export const chatApi = {
  query: (payload: { sessionId: string; chatInput: string; images: string[]; chatId?: string | null; history?: HistoryMessage[]; modelId?: string; knowledgeBaseId?: string }) => api.post<ChatQueryResponse>('/api/chat/query', payload).then((r) => r.data),
}
