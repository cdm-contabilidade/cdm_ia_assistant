import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Header } from './Header'

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useTheme: vi.fn(),
}))

vi.mock('../contexts/AuthContext', () => ({ useAuth: mocks.useAuth }))
vi.mock('../contexts/ThemeContext', () => ({ useTheme: mocks.useTheme }))

const user = { id: 'user-1', name: 'Ana Souza', email: 'ana@example.com', role: 'collaborator' as const, is_active: true, is_blacklisted: false, created_at: '2025-01-01' }

function renderHeader(overrides: { authenticated?: boolean } = {}) {
  const onLogin = vi.fn()
  const toggleTheme = vi.fn()
  const logout = vi.fn()
  mocks.useAuth.mockReturnValue({ user: overrides.authenticated ? user : null, status: overrides.authenticated ? 'authenticated' : 'guest', logout })
  mocks.useTheme.mockReturnValue({ theme: 'light', toggleTheme })
  render(<Header onMenu={vi.fn()} onLogin={onLogin} />)
  return { logout, onLogin, toggleTheme }
}

describe('Header', () => {
  beforeEach(() => vi.clearAllMocks())

  it('keeps the theme control in the fixed header and opens login for guests', async () => {
    const userEventSetup = userEvent.setup()
    const { onLogin, toggleTheme } = renderHeader()
    const header = screen.getByRole('banner')

    expect(header).toHaveClass('sticky', 'top-0')
    await userEventSetup.click(screen.getByRole('button', { name: 'Ativar tema escuro' }))
    await userEventSetup.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(toggleTheme).toHaveBeenCalledOnce()
    expect(onLogin).toHaveBeenCalledOnce()
  })

  it('shows the authenticated user and exposes logout beside the theme', async () => {
    const userEventSetup = userEvent.setup()
    const { logout, onLogin } = renderHeader({ authenticated: true })

    expect(screen.getByText('Ana Souza')).toBeInTheDocument()
    expect(screen.getByText('ana@example.com')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Entrar' })).not.toBeInTheDocument()
    await userEventSetup.click(screen.getByRole('button', { name: 'Sair' }))

    expect(logout).toHaveBeenCalledOnce()
    expect(onLogin).not.toHaveBeenCalled()
  })
})
