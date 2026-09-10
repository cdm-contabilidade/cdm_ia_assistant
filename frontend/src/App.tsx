import { useEffect, useState } from 'react'
import { AdminPanel } from './components/AdminPanel'
import { AuthModal } from './components/AuthModal'
import { ChatArea } from './components/ChatArea'
import { Sidebar } from './components/Sidebar'

import { useAuth } from './contexts/AuthContext'
export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const [adminOpen, setAdminOpen] = useState(false)
  const { user } = useAuth()
  useEffect(() => { if (user?.role !== 'admin') setAdminOpen(false) }, [user])
  return <div className="flex min-h-[100dvh] overflow-hidden bg-canvas text-charcoal dark:bg-dark-canvas dark:text-slate-100"><Sidebar open={sidebarOpen} collapsed={sidebarCollapsed} onClose={() => setSidebarOpen(false)} onToggle={() => setSidebarCollapsed((current) => !current)} onLogin={() => setAuthOpen(true)} onAdmin={() => setAdminOpen(true)} />{adminOpen ? <AdminPanel onClose={() => setAdminOpen(false)} /> : <ChatArea onMenu={() => setSidebarOpen(true)} />}{authOpen && <AuthModal onClose={() => setAuthOpen(false)} />}</div>
}
