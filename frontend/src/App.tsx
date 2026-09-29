import { useCallback, useEffect, useState } from 'react'
import { AdminPanel } from './components/AdminPanel'
import { ChangePasswordModal } from './components/ChangePasswordModal'
import { LoginPage } from './components/LoginPage'
import { ChatArea } from './components/ChatArea'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { Toast, type ToastData } from './components/Toast'

import { useAuth } from './contexts/AuthContext'
import { useChat } from './contexts/ChatContext'
export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [adminOpen, setAdminOpen] = useState(false)
  const [passwordModalOpen, setPasswordModalOpen] = useState(false)
  const [toast, setToast] = useState<ToastData | null>(null)
  const { user, status: authStatus } = useAuth()
  const { knowledgeBases, knowledgeBaseId } = useChat()
  const [returnTo] = useState(() => `${window.location.pathname || '/'}${window.location.search}${window.location.hash}`)
  const activeRagLabel = knowledgeBases.find((knowledgeBase) => knowledgeBase.id === knowledgeBaseId)?.name
  const notify = useCallback((nextToast: ToastData) => setToast(nextToast), [])
  const dismissToast = useCallback(() => setToast(null), [])
  useEffect(() => { if (user?.role !== 'admin') setAdminOpen(false) }, [user])
  if (authStatus === 'loading') return <main className="flex min-h-[100dvh] items-center justify-center bg-canvas text-charcoal dark:bg-dark-canvas dark:text-slate-100" aria-busy="true" aria-label="Carregando sessão"><span className="sr-only">Verificando sua sessão...</span></main>
  if (authStatus !== 'authenticated' || !user) return <LoginPage redirectTarget={returnTo} />
  return <div className="flex h-[100dvh] overflow-hidden bg-canvas text-charcoal dark:bg-dark-canvas dark:text-slate-100"><Sidebar open={sidebarOpen} collapsed={sidebarCollapsed} onClose={() => setSidebarOpen(false)} onToggle={() => setSidebarCollapsed((current) => !current)} onAdmin={() => setAdminOpen(true)} onNotify={notify} /><div className="flex min-h-0 min-w-0 flex-1 flex-col"><Header onMenu={() => setSidebarOpen(true)} ragLabel={activeRagLabel} onChangePassword={() => setPasswordModalOpen(true)} /><div className="flex min-h-0 flex-1 flex-col">{adminOpen ? <AdminPanel onClose={() => setAdminOpen(false)} /> : <ChatArea />}</div></div>{toast && <Toast toast={toast} onDismiss={dismissToast} />}{passwordModalOpen && <ChangePasswordModal onClose={() => setPasswordModalOpen(false)} />}</div>
}
