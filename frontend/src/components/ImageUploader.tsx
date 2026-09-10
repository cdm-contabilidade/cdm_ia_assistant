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

export function ImageUploader({ value, onChange }: { value: ImageAttachment | null; onChange: (value: ImageAttachment | null) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  async function onFileChange(event: React.ChangeEvent<HTMLInputElement>) { const file = event.target.files?.[0]; if (!file) return; try { setError(null); onChange(await readImage(file)) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Imagem inválida.') } finally { event.target.value = '' } }
  return <div className="flex flex-wrap items-center gap-2"><input ref={inputRef} type="file" accept="image/png,image/jpeg" onChange={onFileChange} className="sr-only" aria-label="Selecionar imagem" />{value ? <div className="flex items-center gap-2 rounded-control border border-border bg-white p-1.5 dark:border-dark-border dark:bg-slate-900"><img src={value.dataUrl} alt="Prévia da imagem anexada" className="h-10 w-10 rounded object-cover" /><span className="max-w-32 truncate text-xs text-secondary dark:text-slate-300">{value.name}</span><button type="button" onClick={() => onChange(null)} className="rounded p-1 text-secondary hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/10" aria-label="Remover imagem"><X size={16} /></button></div> : <button type="button" onClick={() => inputRef.current?.click()} className="inline-flex items-center gap-2 rounded-control px-2 py-1.5 text-sm text-secondary hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/10"><ImagePlus size={18} />Imagem</button>}{error && <span role="alert" className="text-xs text-red-700 dark:text-red-300">{error}</span>}</div>
}
