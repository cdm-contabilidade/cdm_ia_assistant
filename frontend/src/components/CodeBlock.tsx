import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

export function CodeBlock({ language, code }: { language?: string; code: string }) {
  const [copied, setCopied] = useState(false)
  async function copyCode() {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }
  return <div className="markdown-code-panel my-3 overflow-hidden rounded-control bg-navy text-slate-100"><div className="flex items-center justify-between border-b border-white/10 px-3 py-2 text-xs text-slate-300"><span>{language || 'código'}</span><button type="button" onClick={copyCode} className="inline-flex items-center gap-1 rounded px-2 py-1 hover:bg-white/10" aria-label="Copiar código">{copied ? <Check size={14} /> : <Copy size={14} />}{copied ? 'Copiado' : 'Copiar'}</button></div><pre className="markdown-code-block p-4 text-sm leading-6"><code>{code}</code></pre></div>
}
