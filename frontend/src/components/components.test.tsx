import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AccessManagementPanel } from './AccessManagementPanel'
import { AdminPanel } from './AdminPanel'
import { ChangePasswordModal } from './ChangePasswordModal'
import { InputBox } from './InputBox'
import { MessageBubble } from './MessageBubble'
import { ThinkingIndicator } from './ChatArea'
import { MarkdownRenderer } from './MarkdownRenderer'
import { adminApi, catalogsApi } from '../services/api'

const authMocks = vi.hoisted(() => ({ changePassword: vi.fn() }))
vi.mock('../contexts/AuthContext', () => ({ useAuth: () => ({ changePassword: authMocks.changePassword }) }))


describe('chat surface behavior', () => {
  it('renders GFM tables inside a contained scroll region', () => {
    render(<MarkdownRenderer content={'| Campo | Valor |\n| --- | --- |\n| status | ok |\n\n```ts\nconst answer = true\n```'} />)
    expect(screen.getByText('status')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Tabela com rolagem horizontal' })).toContainElement(screen.getByRole('table'))
    expect(screen.getByText('Copiar')).toBeInTheDocument()
  })

  it('changes the authenticated user password from the modal', async () => {
    const user = userEvent.setup()
    authMocks.changePassword.mockResolvedValue(undefined)
    const onClose = vi.fn()
    render(<ChangePasswordModal onClose={onClose} />)

    await user.type(screen.getByLabelText('Senha atual'), 'old-pass-8')
    await user.type(screen.getByLabelText('Nova senha'), 'new-pass-8')
    await user.type(screen.getByLabelText('Confirmar nova senha'), 'new-pass-8')
    await user.click(screen.getByRole('button', { name: 'Salvar nova senha' }))

    expect(authMocks.changePassword).toHaveBeenCalledWith('old-pass-8', 'new-pass-8')
    expect(onClose).toHaveBeenCalled()
  })

  it('sends on Enter but preserves Shift+Enter', async () => {
    const user = userEvent.setup(); const onSend = vi.fn().mockResolvedValue(undefined)
    render(<InputBox disabled={false} onSend={onSend} aiModels={[{ id: 'openai-1', provider: 'openai', name: 'OpenAI' }]} modelId="openai-1" />)
    const input = screen.getByLabelText('Mensagem')
    await user.type(input, 'linha 1')
    await user.keyboard('{Shift>}{Enter}{/Shift}linha 2')
    expect(onSend).not.toHaveBeenCalled()
    await user.keyboard('{Enter}')
    expect(onSend).toHaveBeenCalledWith('linha 1\nlinha 2', null)
  })

  it('adds a pasted PNG as a preview without sending it', async () => {
    vi.stubGlobal('FileReader', class {
      result: string | null = null
      onload: (() => void) | null = null
      onerror: (() => void) | null = null

      readAsDataURL() {
        this.result = 'data:image/png;base64,AAAA'
        this.onload?.()
      }
    })
    vi.stubGlobal('Image', class {
      width = 640
      height = 480
      onload: (() => void) | null = null
      onerror: (() => void) | null = null

      set src(_value: string) {
        this.onload?.()
      }
    })
    const drawImage = vi.fn()
    const getContext = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage } as unknown as CanvasRenderingContext2D)
    const onSend = vi.fn().mockResolvedValue(undefined)
    const file = new File(['png'], 'captura.png', { type: 'image/png' })
    render(<InputBox disabled={false} onSend={onSend} aiModels={[{ id: 'openai-1', provider: 'openai', name: 'OpenAI' }]} modelId="openai-1" />)
    const input = screen.getByLabelText('Mensagem')

    try {
      fireEvent.paste(input, { clipboardData: { items: [{ kind: 'file', getAsFile: () => file }] } })

      expect(await screen.findByRole('img', { name: 'Prévia 1: captura.png' })).toBeInTheDocument()
      expect(screen.getByLabelText('1 anexo')).toBeInTheDocument()
      expect(input).toHaveValue('')
      expect(onSend).not.toHaveBeenCalled()
    } finally {
      getContext.mockRestore()
      vi.unstubAllGlobals()
    }
  })

  it('keeps plain text paste native in the composer', async () => {
    const user = userEvent.setup()
    render(<InputBox disabled={false} onSend={vi.fn().mockResolvedValue(undefined)} />)
    const input = screen.getByLabelText('Mensagem')

    await user.click(input)
    await user.paste('texto colado')

    expect(input).toHaveValue('texto colado')
  })
  it('keeps an active Gemini model editable when a sidebar RAG is active', () => {
    render(<InputBox disabled={false} onSend={vi.fn().mockResolvedValue(undefined)} aiModels={[{ id: 'gemini-1', provider: 'gemini', name: 'Gemini' }]} modelId="gemini-1" knowledgeBaseId="rag-1" />)

    expect(screen.queryByRole('combobox', { name: 'RAG Google (opcional)' })).not.toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Modelo' })).not.toBeDisabled()
    expect(screen.getByText('RAG selecionado: escolha um modelo Gemini ativo para este Store.')).toBeInTheDocument()
  })

  it('offers only OpenAI models without a selected RAG', () => {
    render(<InputBox disabled={false} onSend={vi.fn().mockResolvedValue(undefined)} aiModels={[
      { id: 'gemini-1', provider: 'gemini', name: 'Gemini' },
      { id: 'openai-1', provider: 'openai', name: 'OpenAI' },
    ]} />)

    expect(screen.queryByRole('option', { name: /Gemini/ })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'OpenAI · openai' })).toBeInTheDocument()
  })

  it('renders grounded sources as accessible safe links', () => {
    render(<MessageBubble message={{ id: '1', role: 'assistant', content: 'Resposta', created_at: new Date().toISOString(), has_image: false, sources: [{ title: 'Manual CDM', uri: 'https://example.test/manual' }, { title: 'Fonte insegura', uri: 'javascript:alert(1)' }] }} />)
    expect(screen.getByRole('heading', { name: 'Fontes consultadas' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Abrir fonte' })).toHaveAttribute('href', 'https://example.test/manual')
    expect(screen.getByText('Fonte insegura')).toBeInTheDocument()
  })

  it('copies assistant responses and does not show the action for user messages', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
    render(<><MessageBubble message={{ id: 'assistant-1', role: 'assistant', content: 'Resposta para copiar', created_at: new Date().toISOString(), has_image: false }} /><MessageBubble message={{ id: 'user-1', role: 'user', content: 'Pergunta', created_at: new Date().toISOString(), has_image: false }} /></>)
    await user.click(screen.getByRole('button', { name: 'Copiar resposta' }))
    expect(writeText).toHaveBeenCalledWith('Resposta para copiar')
    expect(screen.getByRole('button', { name: 'Resposta copiada' })).toHaveTextContent('Copiado')
    expect(screen.queryByRole('button', { name: 'Copiar resposta' })).not.toBeInTheDocument()
  })

  it('renders the empty collaborator state', async () => {
    vi.spyOn(adminApi, 'users').mockResolvedValue([])
    render(<AdminPanel onClose={vi.fn()} />)
    expect(await screen.findByText('Nenhum colaborador cadastrado.')).toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('lets an admin reset a pending password request', async () => {
    const user = userEvent.setup()
    vi.spyOn(adminApi, 'users').mockResolvedValue([])
    vi.spyOn(adminApi, 'passwordResetRequests').mockResolvedValue([{ id: 'reset-1', email: 'ana@example.com', name: 'Ana', created_at: new Date().toISOString() }])
    const resetPassword = vi.spyOn(adminApi, 'resetPassword').mockResolvedValue({} as never)
    render(<AdminPanel onClose={vi.fn()} />)

    await user.click(screen.getByRole('tab', { name: 'Senhas' }))
    expect(await screen.findByText('ana@example.com')).toBeInTheDocument()
    await user.type(screen.getByPlaceholderText('Nova senha (mínimo 8 caracteres)'), 'temporary-pass')
    await user.click(screen.getByRole('button', { name: 'Redefinir senha' }))
    expect(resetPassword).toHaveBeenCalledWith('reset-1', 'temporary-pass')
    vi.restoreAllMocks()
  })

  it('creates a group and keeps its access rules explicit', async () => {
    vi.spyOn(adminApi, 'groups').mockResolvedValue([])
    vi.spyOn(catalogsApi, 'knowledgeBases').mockResolvedValue([])
    vi.spyOn(adminApi, 'createGroup').mockResolvedValue({ id: 'group-1', name: 'Comercial', userIds: [], knowledgeBaseIds: [], webSearch: false })
    const user = userEvent.setup()
    render(<AccessManagementPanel users={[{ id: 'user-1', name: 'Ana', email: 'ana@testes.dev', role: 'collaborator', is_active: true, is_blacklisted: false, created_at: '' }]} />)
    await user.type(screen.getByLabelText('Nome do grupo'), 'Comercial')
    await user.click(screen.getByRole('button', { name: 'Criar grupo' }))
    expect(await screen.findByText('Regra do grupo')).toBeInTheDocument()
    expect(adminApi.createGroup).toHaveBeenCalledWith({ name: 'Comercial' })
    vi.restoreAllMocks()
  })

  it('shows the assistant thinking state with three animated dots', () => {
    const { container } = render(<ThinkingIndicator />)

    expect(screen.getByRole('status', { name: 'O assistente está pensando' })).toBeInTheDocument()
    expect(container.querySelectorAll('.thinking-dot')).toHaveLength(3)
  })

  it('opens the image viewer from a thumbnail and navigates with arrows', async () => {
    const user = userEvent.setup()
    render(<MessageBubble message={{ id: 'user-1', role: 'user', content: 'Pergunta com imagens', created_at: new Date().toISOString(), has_image: true, imageUrls: ['data:image/png;base64,aaa', 'data:image/png;base64,bbb'] }} />)

    await user.click(screen.getByRole('button', { name: 'Ampliar imagem 1' }))
    expect(screen.getByRole('dialog')).toHaveTextContent('1 de 2')
    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('dialog')).toHaveTextContent('2 de 2')
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
