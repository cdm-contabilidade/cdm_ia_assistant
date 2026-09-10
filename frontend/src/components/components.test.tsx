import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AdminPanel } from './AdminPanel'
import { InputBox } from './InputBox'
import { MessageBubble } from './MessageBubble'
import { MarkdownRenderer } from './MarkdownRenderer'
import { adminApi } from '../services/api'

describe('chat surface behavior', () => {
  it('renders GFM tables and code blocks', () => {
    render(<MarkdownRenderer content={'| Campo | Valor |\n| --- | --- |\n| status | ok |\n\n```ts\nconst answer = true\n```'} />)
    expect(screen.getByText('status')).toBeInTheDocument()
    expect(screen.getByText('Copiar')).toBeInTheDocument()
  })

  it('sends on Enter but preserves Shift+Enter', async () => {
    const user = userEvent.setup(); const onSend = vi.fn().mockResolvedValue(undefined)
    render(<InputBox disabled={false} onSend={onSend} />)
    const input = screen.getByLabelText('Mensagem')
    await user.type(input, 'linha 1')
    await user.keyboard('{Shift>}{Enter}{/Shift}linha 2')
    expect(onSend).not.toHaveBeenCalled()
    await user.keyboard('{Enter}')
    expect(onSend).toHaveBeenCalledWith('linha 1\nlinha 2', null)
  })

  it('renders grounded sources as accessible safe links', () => {
    render(<MessageBubble message={{ id: '1', role: 'assistant', content: 'Resposta', created_at: new Date().toISOString(), has_image: false, sources: [{ title: 'Manual CDM', uri: 'https://example.test/manual' }, { title: 'Fonte insegura', uri: 'javascript:alert(1)' }] }} />)
    expect(screen.getByRole('heading', { name: 'Fontes consultadas' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Abrir fonte' })).toHaveAttribute('href', 'https://example.test/manual')
    expect(screen.getByText('Fonte insegura')).toBeInTheDocument()
  })

  it('renders the empty collaborator state', async () => {
    vi.spyOn(adminApi, 'users').mockResolvedValue([])
    render(<AdminPanel onClose={vi.fn()} />)
    expect(await screen.findByText('Nenhum colaborador cadastrado.')).toBeInTheDocument()
    vi.restoreAllMocks()
  })
})
