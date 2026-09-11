import { useEffect, useId, useRef } from 'react'

type ConfirmDeleteModalProps = {
  chatTitle: string
  busy: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function ConfirmDeleteModal({ chatTitle, busy, onCancel, onConfirm }: ConfirmDeleteModalProps) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const titleId = useId()
  const descriptionId = useId()

  useEffect(() => {
    cancelRef.current?.focus()
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !busy) onCancel()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [busy, onCancel])

  function handleBackdropMouseDown(event: React.MouseEvent<HTMLDivElement>) {
    if (!busy && event.target === event.currentTarget) onCancel()
  }

  return <div className="fixed inset-0 z-30 flex items-center justify-center bg-navy/55 p-4 dark:bg-black/70" role="presentation" onMouseDown={handleBackdropMouseDown}>
    <section role="dialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={descriptionId} aria-busy={busy} className="w-full max-w-md rounded-container border border-border bg-white p-6 shadow-[0_20px_50px_rgba(10,31,68,0.22)] dark:border-dark-border dark:bg-dark-surface">
      <h2 id={titleId} className="text-xl font-semibold text-navy dark:text-slate-100">Excluir conversa?</h2>
      <p id={descriptionId} className="mt-3 text-sm leading-6 text-secondary dark:text-slate-300">A conversa <strong className="font-semibold text-charcoal dark:text-slate-100">{chatTitle}</strong> e todas as suas mensagens serão excluídas e não poderão ser recuperadas.</p>
      <div className="mt-6 flex justify-end gap-3">
        <button ref={cancelRef} type="button" onClick={onCancel} disabled={busy} className="h-11 rounded-control border border-border px-4 text-sm font-medium text-charcoal transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue/50 active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-50 dark:border-dark-border dark:text-slate-100 dark:hover:bg-white/10">Cancelar</button>
        <button type="button" onClick={onConfirm} disabled={busy} className="h-11 rounded-control bg-wine px-4 text-sm font-medium text-white transition hover:bg-wine-soft focus:outline-none focus:ring-2 focus:ring-wine/50 active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-60">{busy ? 'Excluindo...' : 'Excluir conversa'}</button>
      </div>
    </section>
  </div>
}
