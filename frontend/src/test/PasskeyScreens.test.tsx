import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// Mock api client — inline values to avoid hoisting issues
vi.mock('../api/client', () => ({
  api: {
    passkey: {
      registerOptions: vi.fn(),
      registerVerify: vi.fn(),
      loginOptions: vi.fn(),
      loginVerify: vi.fn(),
      listCredentials: vi.fn(),
      addCredentialOptions: vi.fn(),
      addCredentialVerify: vi.fn(),
      deleteCredential: vi.fn(),
    },
    device: {
      requestCode: vi.fn(),
      poll: vi.fn(),
      authorize: vi.fn(),
    },
  },
}))

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    refreshSession: vi.fn(),
  }),
}))

vi.mock('../lib/webauthn', () => ({
  prepareRegistrationOptions: vi.fn((opts: unknown) => opts),
  prepareAuthenticationOptions: vi.fn((opts: unknown) => opts),
  serializeRegistrationCredential: vi.fn(() => ({ id: 'test', rawId: 'test', type: 'public-key', response: {} })),
  serializeAuthenticationCredential: vi.fn(() => ({ id: 'test', rawId: 'test', type: 'public-key', response: {} })),
}))

import { api } from '../api/client'
import PasskeyRegister from '../screens/PasskeyRegister'
import PasskeyLogin from '../screens/PasskeyLogin'
import PasskeyManage from '../screens/PasskeyManage'
import DeviceCodeEntry from '../components/DeviceCodeEntry'
import PairDevice from '../screens/PairDevice'

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('PasskeyRegister', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders create account button when WebAuthn is supported', () => {
    Object.defineProperty(window, 'PublicKeyCredential', { value: vi.fn(), configurable: true })
    renderWithRouter(<PasskeyRegister />)
    expect(screen.getByText('Create Account')).toBeDefined()
    expect(screen.getByText('Cookie')).toBeDefined()
  })

  it('shows unsupported message when WebAuthn is not available', () => {
    Object.defineProperty(window, 'PublicKeyCredential', { value: undefined, configurable: true })
    renderWithRouter(<PasskeyRegister />)
    expect(screen.getByText(/does not support passkeys/)).toBeDefined()
  })

  it('shows link to sign in', () => {
    Object.defineProperty(window, 'PublicKeyCredential', { value: vi.fn(), configurable: true })
    renderWithRouter(<PasskeyRegister />)
    expect(screen.getByText('Sign In')).toBeDefined()
  })
})

describe('PasskeyLogin', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders sign in button when WebAuthn is supported', () => {
    Object.defineProperty(window, 'PublicKeyCredential', { value: vi.fn(), configurable: true })
    renderWithRouter(<PasskeyLogin />)
    expect(screen.getByText('Sign In')).toBeDefined()
  })

  it('shows unsupported message when WebAuthn is not available', () => {
    Object.defineProperty(window, 'PublicKeyCredential', { value: undefined, configurable: true })
    renderWithRouter(<PasskeyLogin />)
    expect(screen.getByText(/does not support passkeys/)).toBeDefined()
  })

  it('shows link to create account', () => {
    Object.defineProperty(window, 'PublicKeyCredential', { value: vi.fn(), configurable: true })
    renderWithRouter(<PasskeyLogin />)
    expect(screen.getByText('Create Account')).toBeDefined()
  })
})

describe('PasskeyManage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows loading state initially', () => {
    vi.mocked(api.passkey.listCredentials).mockReturnValue(new Promise(() => {}))
    renderWithRouter(<PasskeyManage />)
    expect(screen.getByText('Loading...')).toBeDefined()
  })

  it('renders credentials list', async () => {
    vi.mocked(api.passkey.listCredentials).mockResolvedValue({
      credentials: [
        { id: 1, created_at: '2026-01-01T00:00:00Z', last_used_at: null, is_deletable: false },
        { id: 2, created_at: '2026-01-02T00:00:00Z', last_used_at: '2026-01-03T00:00:00Z', is_deletable: true },
      ],
    })
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByText('2 passkeys registered')).toBeDefined()
    })
    expect(screen.getByText('Passkey #1')).toBeDefined()
    expect(screen.getByText('Passkey #2')).toBeDefined()
  })

  it('shows error when loading fails', async () => {
    vi.mocked(api.passkey.listCredentials).mockRejectedValue(new Error('Network error'))
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeDefined()
    })
  })

  it('renders add passkey button', async () => {
    vi.mocked(api.passkey.listCredentials).mockResolvedValue({ credentials: [] })
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByText('Add Passkey')).toBeDefined()
    })
  })

  it('shows delete button only for deletable credentials', async () => {
    vi.mocked(api.passkey.listCredentials).mockResolvedValue({
      credentials: [
        { id: 1, created_at: '2026-01-01T00:00:00Z', last_used_at: null, is_deletable: false },
        { id: 2, created_at: '2026-01-02T00:00:00Z', last_used_at: null, is_deletable: true },
      ],
    })
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByText('Passkey #2')).toBeDefined()
    })
    const deleteButtons = screen.getAllByText('Delete')
    expect(deleteButtons.length).toBe(1)
  })

  it('calls deleteCredential and reloads on delete after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.passkey.listCredentials).mockResolvedValue({
      credentials: [
        { id: 1, created_at: '2026-01-01T00:00:00Z', last_used_at: null, is_deletable: true },
        { id: 2, created_at: '2026-01-02T00:00:00Z', last_used_at: null, is_deletable: true },
      ],
    })
    vi.mocked(api.passkey.deleteCredential).mockResolvedValue({ message: 'Deleted' })
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByText('Passkey #1')).toBeDefined()
    })
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => {
      expect(api.passkey.deleteCredential).toHaveBeenCalledWith(1)
    })
  })

  it('does not delete when confirmation is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    vi.mocked(api.passkey.listCredentials).mockResolvedValue({
      credentials: [
        { id: 1, created_at: '2026-01-01T00:00:00Z', last_used_at: null, is_deletable: true },
        { id: 2, created_at: '2026-01-02T00:00:00Z', last_used_at: null, is_deletable: true },
      ],
    })
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByText('Passkey #1')).toBeDefined()
    })
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    expect(api.passkey.deleteCredential).not.toHaveBeenCalled()
  })

  it('shows "Never" for null last_used_at', async () => {
    vi.mocked(api.passkey.listCredentials).mockResolvedValue({
      credentials: [
        { id: 1, created_at: '2026-01-01T00:00:00Z', last_used_at: null, is_deletable: false },
      ],
    })
    renderWithRouter(<PasskeyManage />)
    await waitFor(() => {
      expect(screen.getByText('Last used: Never')).toBeDefined()
    })
  })
})

describe('DeviceCodeEntry', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders code input and authorize button', () => {
    renderWithRouter(<DeviceCodeEntry />)
    expect(screen.getByLabelText(/Enter the code/)).toBeDefined()
    expect(screen.getByText('Authorize Device')).toBeDefined()
  })

  it('button is disabled when code is too short', () => {
    renderWithRouter(<DeviceCodeEntry />)
    const button = screen.getByText('Authorize Device')
    expect(button.hasAttribute('disabled')).toBe(true)
  })

  it('uppercases input', () => {
    renderWithRouter(<DeviceCodeEntry />)
    const input = screen.getByLabelText(/Enter the code/) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'abc123' } })
    expect(input.value).toBe('ABC123')
  })

  it('shows success message on authorize', async () => {
    vi.mocked(api.device.authorize).mockResolvedValue({ message: 'Device authorized' })
    renderWithRouter(<DeviceCodeEntry />)
    const input = screen.getByLabelText(/Enter the code/) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'ABC123' } })
    fireEvent.click(screen.getByText('Authorize Device'))
    await waitFor(() => {
      expect(screen.getByText(/authorized successfully/)).toBeDefined()
    })
  })

  it('shows error on failed authorize', async () => {
    vi.mocked(api.device.authorize).mockRejectedValue(new Error('Invalid code'))
    renderWithRouter(<DeviceCodeEntry />)
    const input = screen.getByLabelText(/Enter the code/) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'ABC123' } })
    fireEvent.click(screen.getByText('Authorize Device'))
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeDefined()
    })
  })
})

describe('PairDevice', () => {
  it('renders heading and device code entry', () => {
    renderWithRouter(<PairDevice />)
    expect(screen.getByText('Pair a Device')).toBeDefined()
    expect(screen.getByText('Authorize Device')).toBeDefined()
  })
})
