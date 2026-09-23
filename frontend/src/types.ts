export type UserRole = 'admin' | 'collaborator'
export type User = { id: string; email: string; name: string; role: UserRole; is_active: boolean; is_blacklisted: boolean; created_at: string }
export type AdminUser = User
export type AccessGroup = {
  id: string
  name: string
  userIds: string[]
  knowledgeBaseIds: string[]
  webSearch: boolean
  createdAt?: string
  updatedAt?: string
}
export type PermissionCapability = 'knowledge_base' | 'web_search'
export type PermissionOverride = { id?: string; userId?: string; capability: PermissionCapability; knowledgeBaseId?: string; allowed: boolean }
export type ChatSummary = { id: string; title: string; created_at: string; updated_at: string }
export type MessageRole = 'user' | 'assistant'
export type HistoryMessage = { role: MessageRole; content: string }
export type SourceCitation = { title: string; uri?: string | null; text?: string | null; pageNumber?: number | null }
export type MessageMetadata = {
  knowledge_base_id?: string | null
  knowledge_base_name?: string | null
  model_id?: string | null
  model_display_name?: string | null
  [key: string]: unknown
}
export type Message = { id: string; role: MessageRole; content: string; created_at: string; has_image: boolean; image_metadata?: Record<string, unknown> | null; metadata?: MessageMetadata | null; imageUrls?: string[] | null; imageUrl?: string | null; sources?: SourceCitation[]; modelId?: string | null; knowledgeBaseId?: string | null; modelName?: string | null; knowledgeBaseName?: string | null }

export function normalizeMessage(message: Message): Message {
  const metadata = message.metadata
  return {
    ...message,
    ...(message.modelId !== undefined || metadata?.model_id !== undefined ? { modelId: message.modelId ?? metadata?.model_id ?? null } : {}),
    ...(message.knowledgeBaseId !== undefined || metadata?.knowledge_base_id !== undefined ? { knowledgeBaseId: message.knowledgeBaseId ?? metadata?.knowledge_base_id ?? null } : {}),
    ...(message.modelName !== undefined || metadata?.model_display_name !== undefined ? { modelName: message.modelName ?? metadata?.model_display_name ?? null } : {}),
    ...(message.knowledgeBaseName !== undefined || metadata?.knowledge_base_name !== undefined ? { knowledgeBaseName: message.knowledgeBaseName ?? metadata?.knowledge_base_name ?? null } : {}),
  }
}

export function normalizeMessages(messages: Message[]): Message[] {
  return messages.map(normalizeMessage)
}
export type AiModel = { id: string; provider: string; name: string; displayName?: string; model_id?: string; modelId?: string; active?: boolean; is_active?: boolean; isActive?: boolean }
export type ProviderName = 'gemini' | 'openai'
export type ProviderStatus = { provider: ProviderName; configured: boolean; source: 'database' | 'environment' | 'none'; maskedKey: string | null; updatedAt?: string | null }
export type KnowledgeBase = { id: string; name: string; store_id?: string; storeId?: string; fileSearchStoreId?: string; provider?: string; featured?: boolean; active?: boolean; is_active?: boolean; isActive?: boolean }
export type ImageAttachment = { dataUrl: string; name: string; size: number; mime: 'image/png' | 'image/jpeg'; width?: number; height?: number }
export type ApiError = {
  error?: { code?: string; message?: string; request_id?: string }
  detail?: string | { code?: string; message?: string }
  message?: string
}
export type AuthStatus = 'loading' | 'guest' | 'authenticated'
export type DataStatus = 'loading' | 'ready' | 'error'
export type TokenResponse = { access_token: string; token_type: 'bearer'; user: User }
export type ChatQueryResponse = { sessionId: string; chatId: string | null; title?: string | null; answer: string; messages: Message[]; sources: SourceCitation[]; modelId?: string | null; knowledgeBaseId?: string | null; model?: { name?: string } | null; knowledgeBase?: { name?: string } | null }
