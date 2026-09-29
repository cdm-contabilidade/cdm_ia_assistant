import { LogOut, Menu, Moon, Sun, UserRound } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { RagTag } from './RagTag'

type HeaderProps = { onMenu: () => void; ragLabel?: string; onChangePassword?: () => void }

export function Header({ onMenu, ragLabel, onChangePassword }: HeaderProps) {
  const { user, status, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [accountOpen, setAccountOpen] = useState(false)
  const accountRef = useRef<HTMLDivElement>(null)
  const isAuthenticated = status === 'authenticated' && user

  useEffect(() => {
    if (!accountOpen) return
    function closeOnOutsideClick(event: MouseEvent) {
      if (!accountRef.current?.contains(event.target as Node)) setAccountOpen(false)
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setAccountOpen(false)
    }
    window.addEventListener('mousedown', closeOnOutsideClick)
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      window.removeEventListener('mousedown', closeOnOutsideClick)
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [accountOpen])

  return <header className="sticky top-0 z-10 flex min-h-16 shrink-0 items-center justify-between border-b border-border bg-white/90 px-3 py-2 backdrop-blur dark:border-dark-border dark:bg-dark-surface/95 md:px-6">
    <div className="flex min-w-0 items-center">
      <button type="button" onClick={onMenu} className="mr-3 rounded-control p-2 text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] dark:text-slate-300 dark:hover:bg-white/10 md:hidden" aria-label="Abrir menu"><Menu size={20} /></button>
      <div className="min-w-0"><p className="text-xs font-medium uppercase tracking-[.16em] text-wine">CDM AI</p><h1 className="truncate text-base font-semibold text-navy dark:text-slate-100 sm:text-lg">Assistente de Inteligência Artificial Contábil</h1></div>
    </div>
    <div className="ml-4 flex shrink-0 items-center gap-2">
      <RagTag label={ragLabel} size="subtitle" className="max-w-[min(38vw,16rem)]" />
      <button type="button" onClick={toggleTheme} className="rounded-control p-2 text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] dark:text-slate-300 dark:hover:bg-white/10" aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'} title={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
      {isAuthenticated && <div ref={accountRef} className="relative border-l border-border pl-2 dark:border-dark-border"><button type="button" onClick={() => setAccountOpen((current) => !current)} className="flex items-center gap-2 rounded-control px-2 py-1.5 text-left transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 dark:hover:bg-white/10" aria-label={`Abrir menu de ${user.name}`} aria-haspopup="menu" aria-expanded={accountOpen}><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-wine text-white"><UserRound size={16} aria-hidden="true" /></span><span className="max-w-[150px]"><span className="block truncate text-sm font-medium text-navy dark:text-slate-100">{user.name}</span><span className="block truncate text-xs text-secondary dark:text-slate-400">{user.email}</span></span></button>{accountOpen && <div role="menu" aria-label="Menu do usuário" className="absolute right-0 top-full z-30 mt-2 min-w-[180px] rounded-control border border-border bg-white p-1 shadow-panel dark:border-dark-border dark:bg-dark-surface">{onChangePassword && <button type="button" role="menuitem" onClick={() => { setAccountOpen(false); onChangePassword() }} className="flex w-full items-center gap-2 rounded-control px-3 py-2 text-left text-sm text-charcoal hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 dark:text-slate-100 dark:hover:bg-white/10"><UserRound size={16} aria-hidden="true" />Perfil</button>}<button type="button" role="menuitem" onClick={() => { setAccountOpen(false); void logout() }} className="flex w-full items-center gap-2 rounded-control px-3 py-2 text-left text-sm text-charcoal hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 dark:text-slate-100 dark:hover:bg-white/10"><LogOut size={16} aria-hidden="true" />Sair</button></div>}</div>}
    </div>
  </header>
}
