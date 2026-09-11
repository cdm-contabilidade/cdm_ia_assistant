import { ImagePlus, X } from 'lucide-react'
import { useRef, useState } from 'react'
import type { ImageAttachment } from '../types'

async function readImage(file: File): Promise<ImageAttachment> {
  if (!['image/png', 'image/jpeg'].includes(file.type)) throw new Error('Escolha uma imagem PNG ou JPEG.')
  if (file.size > 5_242_880) throw new Error('A imagem deve ter até 5 MB.')
  const source = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Não foi possível ler a imagem.')); reader.readAsDataURL(file) })
  const image = await new Promise<HTMLImageElement>((resolve, reject) => { const element = new Image(); element.onload = () => resolve(element); element.onerror = () => reject(new Error('A imagem é inválida.')); element.src = source })
  const maxDimension = 1920
  const scale = Math.min(1, maxDimension / Math.max(image.width, image.height))
  const canvas = document.createElement('canvas'); canvas.width = Math.round(image.width * scale); canvas.height = Math.round(image.height * scale)
  canvas.getContext('2d')?.drawImage(image, 0, 0, canvas.width, canvas.height)
  const dataUrl = file.size > 1_500_000 || scale < 1 ? canvas.toDataURL('image/jpeg', .82) : source
  return { dataUrl, name: file.name, size: Math.round((dataUrl.length * 3) / 4), mime: dataUrl.startsWith('data:image/jpeg') ? 'image/jpeg' : 'image/png', width: canvas.width, height: canvas.height }
}

export function ImageUploader({ value, onChange, disabled = false }: { value: ImageAttachment | null; onChange: (value: ImageAttachment | null) => void; disabled?: boolean }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  async function onFileChange(event: React.ChangeEvent<HTMLInputElement>) { const file = event.target.files?.[0]; if (!file) return; try { setError(null); onChange(await readImage(file)) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Imagem inválida.') } finally { event.target.value = '' } }
  return <div className="flex min-w-0 flex-wrap items-center gap-1.5"><input ref={inputRef} type="file" accept="image/png,image/jpeg" onChange={onFileChange} disabled={disabled} className="sr-only" aria-label="Selecionar imagem" />{value ? <div className="flex min-w-0 items-center gap-1.5 rounded-control border border-wine/20 bg-wine/[.04] p-1 dark:border-wine-soft/30 dark:bg-wine/10"><img src={value.dataUrl} alt="Prévia da imagem anexada" className="h-7 w-7 rounded object-cover" /><span className="max-w-28 truncate text-[11px] text-secondary dark:text-slate-300">{value.name}</span><button type="button" onClick={() => onChange(null)} disabled={disabled} className="rounded p-1 text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/40 dark:text-slate-300 dark:hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50" aria-label="Remover imagem"><X size={14} /></button></div> : <button type="button" onClick={() => inputRef.current?.click()} disabled={disabled} className="inline-flex h-8 items-center gap-1.5 rounded-control px-2 text-xs font-medium text-secondary transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/40 dark:text-slate-300 dark:hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"><ImagePlus size={16} aria-hidden="true" />Imagem</button>}{error && <span role="alert" className="basis-full text-[11px] text-red-700 dark:text-red-300">{error}</span>}</div>
}
