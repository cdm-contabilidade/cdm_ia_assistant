import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { chatApi, chatsApi, getApiError } from '../services/api'
import { useAuth } from './AuthContext'
import type { ChatSummary, DataStatus, ImageAttachment, Message } from '../types'

type ChatContextValue = {
  sessionId: string
  chats: ChatSummary[]
  activeChatId: string | null
  messages: Message[]
  status: DataStatus
  error: string | null
  isSending: boolean
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

  useEffect(() => {
    if (authStatus === 'loading') return
    setError(null)
    if (!user) {
      const next = sessionStorage.getItem(SESSION_KEY) || newSession()
      setSessionId(next); setChats([]); setActiveChatId(null); setMessages(readGuestMessages()); setStatus('ready'); return
    }
    setStatus('loading')
    chatsApi.list().then(async (items) => {
      setChats(items)
      const first = items[0]
      if (first) { setActiveChatId(first.id); setMessages(await chatsApi.messages(first.id)) }
      else { setActiveChatId(null); setMessages([]) }
      setStatus('ready')
    }).catch((cause) => { setStatus('error'); setError(getApiError(cause)) })
  }, [authStatus, user])

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
  const deleteChat = useCallback(async (id: string) => { await chatsApi.remove(id); const remaining = chats.filter((chat) => chat.id !== id); setChats(remaining); if (activeChatId === id) { setActiveChatId(remaining[0]?.id || null); setMessages(remaining[0] ? await chatsApi.messages(remaining[0].id) : []) } }, [activeChatId, chats])
  const sendMessage = useCallback(async (text: string, image: ImageAttachment | null) => {
    const clean = text.trim(); if (!clean || isSending) return
    const optimistic: Message = { id: crypto.randomUUID(), role: 'user', content: clean, created_at: new Date().toISOString(), has_image: Boolean(image), image_metadata: image ? { mime: image.mime, size: image.size, width: image.width, height: image.height } : null, imageUrl: image?.dataUrl }
    const history = user ? undefined : messages.slice(-20).map(({ role, content }) => ({ role, content }))
    setMessages((current) => [...current, optimistic]); setIsSending(true); setError(null)
    try {
      const result = await chatApi.query({ sessionId, chatInput: clean, image: image?.dataUrl || null, chatId: user ? activeChatId : null, ...(history ? { history } : {}) })
      setMessages((current) => [...current.filter((message) => message.id !== optimistic.id), ...result.messages.map((message) => message.role === 'user' ? { ...message, imageUrl: image?.dataUrl } : { ...message, sources: result.sources })])
      if (user && result.chatId && !chats.some((chat) => chat.id === result.chatId)) setChats((current) => [{ id: result.chatId!, title: clean.slice(0, 255), created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, ...current])
      if (result.chatId) setActiveChatId(result.chatId)
    } catch (cause) { setMessages((current) => current.filter((message) => message.id !== optimistic.id)); setError(getApiError(cause)) }
    finally { setIsSending(false) }
  }, [activeChatId, chats, isSending, messages, sessionId, user])
  const value = useMemo(() => ({ sessionId, chats, activeChatId, messages, status, error, isSending, selectChat, createChat, renameChat, deleteChat, sendMessage }), [sessionId, chats, activeChatId, messages, status, error, isSending, selectChat, createChat, renameChat, deleteChat, sendMessage])
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() { const context = useContext(ChatContext); if (!context) throw new Error('useChat must be used within ChatProvider'); return context }
