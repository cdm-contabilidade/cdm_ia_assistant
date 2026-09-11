import { Database } from 'lucide-react'

type RagTagProps = { label?: string; className?: string; size?: 'compact' | 'subtitle' }

export function RagTag({ label, className = '', size = 'compact' }: RagTagProps) {
  if (!label) return null
  return <span className={`inline-flex max-w-full items-center gap-1 rounded-full border border-wine/25 bg-wine/[.07] font-semibold text-wine dark:border-wine-soft/40 dark:bg-wine-soft/15 dark:text-rose-100 ${size === 'subtitle' ? 'rounded-control px-2.5 py-0.5 text-xs leading-5' : 'px-2 py-0.5 text-[10px] leading-4'} ${className}`} aria-label={`RAG: ${label}`}><Database size={size === 'subtitle' ? 13 : 11} aria-hidden="true" /><span className="truncate">{label}</span></span>
}
