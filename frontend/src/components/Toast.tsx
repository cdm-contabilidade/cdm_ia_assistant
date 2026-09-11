import { AlertCircle, CheckCircle2, X } from 'lucide-react'
import { useEffect } from 'react'

export type ToastTone = 'success' | 'error'
export type ToastData = { tone: ToastTone; message: string }

type ToastProps = {
  toast: ToastData
  onDismiss: () => void
}

export function Toast({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const timeoutId = window.setTimeout(onDismiss, 4000)
    return () => window.clearTimeout(timeoutId)
  }, [onDismiss, toast])

  const isError = toast.tone === 'error'
  return <div className="fixed bottom-4 right-4 z-40 w-[min(calc(100vw-2rem),24rem)]" role={isError ? 'alert' : 'status'}>
    <div className={`flex items-start gap-3 rounded-container border bg-white p-4 shadow-[0_16px_36px_rgba(10,31,68,0.18)] dark:bg-dark-surface ${isError ? 'border-red-200 dark:border-red-900/70' : 'border-blue/25 dark:border-blue/40'}`}>
      {isError ? <AlertCircle size={20} className="mt-0.5 shrink-0 text-red-600 dark:text-red-300" aria-hidden="true" /> : <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-blue dark:text-blue" aria-hidden="true" />}
      <p className={`min-w-0 flex-1 text-sm leading-5 ${isError ? 'text-red-800 dark:text-red-100' : 'text-charcoal dark:text-slate-100'}`}>{toast.message}</p>
      <button type="button" onClick={onDismiss} className="-mr-1 -mt-1 rounded-control p-1.5 text-secondary transition hover:bg-slate-100 hover:text-charcoal focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white" aria-label="Fechar aviso" title="Fechar aviso"><X size={16} /></button>
    </div>
  </div>
}
