import { LogOut, Menu, Moon, Sun } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { RagTag } from './RagTag'

type HeaderProps = { onMenu: () => void; ragLabel?: string }

export function Header({ onMenu, ragLabel }: HeaderProps) {
  const { user, status, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const isAuthenticated = status === 'authenticated' && user

  return <header className="sticky top-0 z-10 flex min-h-16 shrink-0 items-center justify-between border-b border-border bg-white/90 px-3 py-2 backdrop-blur dark:border-dark-border dark:bg-dark-surface/95 md:px-6">
    <div className="flex min-w-0 items-center">
      <button type="button" onClick={onMenu} className="mr-3 rounded-control p-2 text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] dark:text-slate-300 dark:hover:bg-white/10 md:hidden" aria-label="Abrir menu"><Menu size={20} /></button>
      <div className="min-w-0"><p className="text-xs font-medium uppercase tracking-[.16em] text-wine">CDM AI</p><h1 className="truncate text-base font-semibold text-navy dark:text-slate-100 sm:text-lg">Assistente de Inteligência Artificial Contábil</h1></div>
    </div>
    <div className="ml-4 flex shrink-0 items-center gap-2">
      <RagTag label={ragLabel} size="subtitle" className="max-w-[min(38vw,16rem)]" />
      <button type="button" onClick={toggleTheme} className="rounded-control p-2 text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] dark:text-slate-300 dark:hover:bg-white/10" aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'} title={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
      {isAuthenticated && <div className="flex items-center gap-2 border-l border-border pl-2 dark:border-dark-border"><div className="hidden max-w-[180px] text-right sm:block"><p className="truncate text-sm font-medium text-navy dark:text-slate-100">{user.name}</p><p className="truncate text-xs text-secondary dark:text-slate-400">{user.email}</p></div><button type="button" onClick={() => void logout()} className="rounded-control p-2 text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] dark:text-slate-300 dark:hover:bg-white/10" aria-label="Sair" title="Sair"><LogOut size={18} /></button></div>}
    </div>
  </header>
}
