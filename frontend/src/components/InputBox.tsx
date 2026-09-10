import { Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { ImageAttachment } from '../types'
import { ImageUploader } from './ImageUploader'

export function InputBox({ disabled, onSend }: { disabled: boolean; onSend: (text: string, image: ImageAttachment | null) => Promise<void> }) {
  const [text, setText] = useState('')
  const [image, setImage] = useState<ImageAttachment | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { const node = textareaRef.current; if (!node) return; node.style.height = 'auto'; node.style.height = `${Math.min(node.scrollHeight, 144)}px` }, [text])
  async function send() { if (!text.trim() || disabled) return; const currentText = text; const currentImage = image; setText(''); setImage(null); try { await onSend(currentText, currentImage) } catch { setText(currentText); setImage(currentImage) } }
  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void send() } }
  return <div className="rounded-container border border-border bg-white p-3 shadow-panel dark:border-dark-border dark:bg-dark-surface"><textarea ref={textareaRef} value={text} onChange={(event) => setText(event.target.value)} onKeyDown={onKeyDown} disabled={disabled} rows={1} maxLength={10000} placeholder="Escreva sua consulta..." aria-label="Mensagem" className="max-h-36 min-h-11 w-full resize-none border-0 bg-transparent px-1 py-2 text-[15px] leading-6 text-charcoal placeholder:text-secondary/70 focus:outline-none dark:text-slate-100 dark:placeholder:text-slate-400 disabled:cursor-not-allowed disabled:opacity-60" /><div className="flex items-center justify-between gap-3 border-t border-border pt-2 dark:border-dark-border"><ImageUploader value={image} onChange={setImage} /><div className="flex items-center gap-3"><span className="hidden text-xs text-secondary dark:text-slate-400 sm:inline">Enter envia · Shift+Enter quebra</span><button type="button" onClick={() => void send()} disabled={disabled || !text.trim()} className="inline-flex h-10 items-center gap-2 rounded-control bg-blue px-4 text-sm font-medium text-white transition hover:bg-navy disabled:cursor-not-allowed disabled:opacity-50" aria-label="Enviar mensagem">{disabled ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : <Send size={16} />}Enviar</button></div></div></div>
}
