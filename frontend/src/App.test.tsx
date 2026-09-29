import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useChat: vi.fn(),
  requestPasswordReset: vi.fn(),
}))

vi.mock('./contexts/AuthContext', () => ({ useAuth: mocks.useAuth }))
vi.mock('./contexts/ChatContext', () => ({ useChat: mocks.useChat }))
vi.mock('./services/api', () => ({ authApi: { requestPasswordReset: mocks.requestPasswordReset }, getApiError: (error: { message?: string }) => error.message || 'Erro' }))

function renderApp(status: 'loading' | 'guest' | 'authenticated' = 'guest') {
  mocks.useAuth.mockReturnValue({
    user: status === 'authenticated' ? { id: 'user-1', name: 'Ana Souza', email: 'ana@example.com', role: 'collaborator', is_active: true, is_blacklisted: false, created_at: '2025-01-01' } : null,
    status,
    error: null,
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
  })
  mocks.useChat.mockReturnValue({ knowledgeBases: [], knowledgeBaseId: '' })
  return render(<App />)
}

describe('application authentication gate', () => {
  afterEach(() => window.history.replaceState(null, '', '/'))

  it('does not render application content while the session is loading', () => {
    renderApp('loading')

    expect(screen.getByRole('main', { name: 'Carregando sessão' })).toBeInTheDocument()
    expect(screen.queryByText('Assistente de Inteligência Artificial Contábil')).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Entrar na sua conta' })).not.toBeInTheDocument()
  })

  it('shows the dedicated login page to guests', () => {
    renderApp()

    expect(screen.getByRole('heading', { name: 'Entrar na sua conta' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Email' })).toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
    expect(screen.queryByText('Assistente de Inteligência Artificial Contábil')).not.toBeInTheDocument()
  })

  it('keeps the originally requested pathname, search, and hash after login', async () => {
    window.history.replaceState(null, '', '/requested?tab=recent#reply')
    const user = userEvent.setup()
    renderApp()

    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(window.location.pathname).toBe('/requested')
    expect(window.location.search).toBe('?tab=recent')
    expect(window.location.hash).toBe('#reply')
  })
})


  it('submits a forgotten password request with a generic confirmation', async () => {
    const user = userEvent.setup()
    mocks.requestPasswordReset.mockResolvedValue({ message: 'Se o email estiver cadastrado, o administrador será notificado.' })
    renderApp()

    await user.click(screen.getByRole('button', { name: 'Esqueci minha senha' }))
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'ana@example.com')
    await user.click(screen.getByRole('button', { name: 'Solicitar recuperação' }))

    expect(mocks.requestPasswordReset).toHaveBeenCalledWith('ana@example.com')
    expect(screen.getByRole('status')).toHaveTextContent('administrador será notificado')
  })
