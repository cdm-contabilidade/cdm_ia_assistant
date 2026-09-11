import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { catalogsApi, chatApi, chatsApi, getApiError } from '../services/api'
import { useAuth } from './AuthContext'
import type { AiModel, ChatSummary, DataStatus, ImageAttachment, KnowledgeBase, Message } from '../types'

type ChatContextValue = {
  sessionId: string
  chats: ChatSummary[]
  activeChatId: string | null
  messages: Message[]
  status: DataStatus
  error: string | null
  isSending: boolean
  catalogsLoading: boolean
  aiModels: AiModel[]
  knowledgeBases: KnowledgeBase[]
  modelId: string
  knowledgeBaseId: string
  setModelId: (id: string) => void
  setKnowledgeBaseId: (id: string) => void
  selectChat: (id: string | null) => Promise<void>
  createChat: () => Promise<void>
  renameChat: (id: string, title: string) => Promise<void>
  deleteChat: (id: string) => Promise<void>
  sendMessage: (text: string, image: ImageAttachment | null) => Promise<void>
}
const ChatContext = createContext<ChatContextValue | null>(null)
const SESSION_KEY = 'guest_session_id'
const MESSAGES_KEY = 'guest_messages'
const ACTIVE_KEY = 'guest_active_chat'

function newSession() { return crypto.randomUUID() }
function readGuestMessages(): Message[] { try { return JSON.parse(sessionStorage.getItem(MESSAGES_KEY) || '[]') as Message[] } catch { return [] } }
function saveGuest(sessionId: string, messages: Message[], active: string | null) { sessionStorage.setItem(SESSION_KEY, sessionId); sessionStorage.setItem(MESSAGES_KEY, JSON.stringify(messages)); sessionStorage.setItem(ACTIVE_KEY, active || '') }

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user, status: authStatus } = useAuth()
  const [sessionId, setSessionId] = useState(() => sessionStorage.getItem(SESSION_KEY) || newSession())
  const [chats, setChats] = useState<ChatSummary[]>([])
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState<DataStatus>('loading')
  const [error, setError] = useState<string | null>(null)
  const [isSending, setIsSending] = useState(false)
  const [catalogsLoading, setCatalogsLoading] = useState(true)
  const [aiModels, setAiModels] = useState<AiModel[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [modelId, setModelId] = useState('')
  const [knowledgeBaseId, setKnowledgeBaseId] = useState('')

  useEffect(() => {
    if (authStatus === 'loading') return
    setError(null)

    // Os catálogos são públicos. Eles devem continuar disponíveis para visitantes
    // e não podem impedir a área de conversa quando a sessão expira (401).
    let cancelled = false
    setCatalogsLoading(true)
    void Promise.allSettled([catalogsApi.aiModels(), catalogsApi.knowledgeBases()]).then(([modelsResult, basesResult]) => {
      if (cancelled) return
      if (modelsResult.status === 'fulfilled') {
        const activeModels = modelsResult.value.filter((item) => item.active !== false && item.is_active !== false && item.isActive !== false)
        setAiModels(activeModels)
        setModelId((current) => current && activeModels.some((item) => item.id === current) ? current : activeModels[0]?.id || '')
      }
      if (basesResult.status === 'fulfilled') {
        const activeBases = basesResult.value.filter((item) => item.active !== false && item.is_active !== false && item.isActive !== false)
        setKnowledgeBases(activeBases)
        setKnowledgeBaseId((current) => current && activeBases.some((item) => item.id === current) ? current : '')
      }
      setCatalogsLoading(false)
    })
    if (!user) {
      const next = sessionStorage.getItem(SESSION_KEY) || newSession()
      setSessionId(next); setChats([]); setActiveChatId(null); setMessages(readGuestMessages()); setStatus('ready'); return () => { cancelled = true }
    }
    setStatus('loading')
    chatsApi.list().then(async (items) => {
      setChats(items)
      const first = items[0]
      if (first) { setActiveChatId(first.id); setMessages(await chatsApi.messages(first.id)) }
      else { setActiveChatId(null); setMessages([]) }
      setStatus('ready')
    }).catch((cause) => { setStatus('error'); setError(getApiError(cause)) })
    return () => { cancelled = true }
  }, [authStatus, user])

  const changeModel = useCallback((id: string) => {
    setModelId(id)
    if (id) setKnowledgeBaseId('')
  }, [])

  const changeKnowledgeBase = useCallback((id: string) => {
    setKnowledgeBaseId(id)
    setModelId((current) => id ? '' : current || aiModels[0]?.id || '')
  }, [aiModels])


  useEffect(() => { if (!user && status === 'ready') saveGuest(sessionId, messages, activeChatId) }, [user, status, sessionId, messages, activeChatId])

  const selectChat = useCallback(async (id: string | null) => {
    if (!user) { setActiveChatId(null); setMessages([]); return }
    if (!id) { setActiveChatId(null); setMessages([]); return }
    setStatus('loading'); setError(null)
    try { setMessages(await chatsApi.messages(id)); setActiveChatId(id); setStatus('ready') }
    catch (cause) { setStatus('error'); setError(getApiError(cause)) }
  }, [user])
  const createChat = useCallback(async () => {
    if (!user) { setMessages([]); setActiveChatId(null); return }
    const chat = await chatsApi.create(); setChats((current) => [chat, ...current]); setActiveChatId(chat.id); setMessages([])
  }, [user])
  const renameChat = useCallback(async (id: string, title: string) => { const updated = await chatsApi.rename(id, title); setChats((current) => current.map((chat) => chat.id === id ? updated : chat)) }, [])
  const deleteChat = useCallback(async (id: string) => {
    await chatsApi.remove(id)
    const remaining = chats.filter((chat) => chat.id !== id)
    setChats(remaining)
    if (activeChatId !== id) return

    const nextChatId = remaining[0]?.id ?? null
    setActiveChatId(nextChatId)
    setError(null)
    if (!nextChatId) {
      setMessages([])
      setStatus('ready')
      return
    }

    setStatus('loading')
    try {
      setMessages(await chatsApi.messages(nextChatId))
      setStatus('ready')
    } catch (cause) {
      setMessages([])
      setStatus('error')
      setError(getApiError(cause))
    }
  }, [activeChatId, chats])
  const sendMessage = useCallback(async (text: string, image: ImageAttachment | null) => {
    const clean = text.trim(); if (!clean || isSending) return
    const optimistic: Message = { id: crypto.randomUUID(), role: 'user', content: clean, created_at: new Date().toISOString(), has_image: Boolean(image), image_metadata: image ? { mime: image.mime, size: image.size, width: image.width, height: image.height } : null, imageUrl: image?.dataUrl }
    const history = user ? undefined : messages.slice(-20).map(({ role, content }) => ({ role, content }))
    setMessages((current) => [...current, optimistic]); setIsSending(true); setError(null)
    try {
      const result = await chatApi.query({ sessionId, chatInput: clean, image: image?.dataUrl || null, chatId: user ? activeChatId : null, ...(history ? { history } : {}), ...(modelId ? { modelId } : {}), ...(knowledgeBaseId ? { knowledgeBaseId } : {}) })
      setMessages((current) => [...current.filter((message) => message.id !== optimistic.id), ...result.messages.map((message) => message.role === 'user' ? { ...message, imageUrl: image?.dataUrl } : { ...message, sources: result.sources, modelId: result.modelId, knowledgeBaseId: result.knowledgeBaseId, modelName: result.model?.name, knowledgeBaseName: result.knowledgeBase?.name })])
      if (user && result.chatId && !chats.some((chat) => chat.id === result.chatId)) setChats((current) => [{ id: result.chatId!, title: clean.slice(0, 255), created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, ...current])
      if (result.chatId) setActiveChatId(result.chatId)
    } catch (cause) { setMessages((current) => current.filter((message) => message.id !== optimistic.id)); setError(getApiError(cause)) }
    finally { setIsSending(false) }
  }, [activeChatId, chats, isSending, messages, sessionId, user, modelId, knowledgeBaseId])
  const value = useMemo(() => ({ sessionId, chats, activeChatId, messages, status, error, isSending, catalogsLoading, aiModels, knowledgeBases, modelId, knowledgeBaseId, setModelId: changeModel, setKnowledgeBaseId: changeKnowledgeBase, selectChat, createChat, renameChat, deleteChat, sendMessage }), [sessionId, chats, activeChatId, messages, status, error, isSending, catalogsLoading, aiModels, knowledgeBases, modelId, knowledgeBaseId, changeModel, changeKnowledgeBase, selectChat, createChat, renameChat, deleteChat, sendMessage])
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() { const context = useContext(ChatContext); if (!context) throw new Error('useChat must be used within ChatProvider'); return context }
