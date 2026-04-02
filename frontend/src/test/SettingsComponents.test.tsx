import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'

const { mockToggleTheme, mockApi } = vi.hoisted(() => {
  const mockToggleTheme = vi.fn()
  const mockApi = {
    ai: {
      testApiKey: vi.fn(() => Promise.resolve({ valid: true, message: 'Key is valid' })),
      saveApiKey: vi.fn(() => Promise.resolve({ saved: true })),
      status: vi.fn(() =>
        Promise.resolve({
          available: true,
          configured: true,
          valid: true,
          default_model: 'openai/gpt-4',
          error: null,
          error_code: null,
        }),
      ),
      models: vi.fn(() => Promise.resolve([{ id: 'openai/gpt-4', name: 'GPT-4' }])),
      prompts: {
        list: vi.fn(() => Promise.resolve([])),
        update: vi.fn((type: string, form: Record<string, unknown>) =>
          Promise.resolve({
            prompt_type: type,
            name: 'Test Prompt',
            description: 'A test prompt',
            system_prompt: form.system_prompt,
            user_prompt_template: form.user_prompt_template,
            model: form.model,
            is_active: form.is_active,
          }),
        ),
      },
      quotas: {
        update: vi.fn((limits: Record<string, number>) =>
          Promise.resolve({ limits, usage: { remix: 0, remix_suggestions: 0, scale: 0, tips: 0, discover: 0, timer: 0 }, unlimited: false, resets_at: '2026-04-03T00:00:00Z' }),
        ),
      },
    },
    sources: {
      list: vi.fn(() => Promise.resolve([])),
      toggle: vi.fn((id: number) => Promise.resolve({ id, is_enabled: true })),
      bulkToggle: vi.fn(() => Promise.resolve([])),
      updateSelector: vi.fn((id: number, selector: string) =>
        Promise.resolve({ id, result_selector: selector }),
      ),
      test: vi.fn(() => Promise.resolve({ success: true, message: 'Source OK' })),
      testAll: vi.fn(() => Promise.resolve({ tested: 2, passed: 2, failed: 0 })),
    },
    profiles: {
      list: vi.fn(() => Promise.resolve([])),
      rename: vi.fn((id: number, name: string) => Promise.resolve({ id, name })),
      setUnlimited: vi.fn((id: number, val: boolean) => Promise.resolve({ id, unlimited_ai: val })),
      deletionPreview: vi.fn(() =>
        Promise.resolve({
          profile: { id: 2, name: 'Alice', avatar_color: '#f00', created_at: '2026-01-01T00:00:00Z' },
          data_to_delete: { remixes: 3, remix_images: 1, favorites: 5, collections: 2, collection_items: 4, view_history: 10, scaling_cache: 0, discover_cache: 0 },
        }),
      ),
      delete: vi.fn(() => Promise.resolve(null)),
    },
    system: {
      resetPreview: vi.fn(() =>
        Promise.resolve({
          data_counts: {
            profiles: 2,
            recipes: 10,
            recipe_images: 5,
            favorites: 8,
            collections: 3,
            view_history: 20,
            ai_suggestions: 4,
            serving_adjustments: 2,
          },
        }),
      ),
      reset: vi.fn(() => Promise.resolve(null)),
    },
    passkey: {
      listCredentials: vi.fn(() =>
        Promise.resolve({
          credentials: [
            { id: 1, created_at: '2026-01-01T00:00:00Z', last_used_at: '2026-03-01T00:00:00Z', is_deletable: true },
            { id: 2, created_at: '2026-02-01T00:00:00Z', last_used_at: null, is_deletable: false },
          ],
        }),
      ),
      addCredentialOptions: vi.fn(),
      addCredentialVerify: vi.fn(),
      deleteCredential: vi.fn(() => Promise.resolve(null)),
    },
  }
  return { mockToggleTheme, mockApi }
})

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock ProfileContext
vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    profile: { id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' },
    theme: 'light',
    toggleTheme: mockToggleTheme,
  }),
}))

// Mock router
vi.mock('../router', () => ({
  useVersion: () => '1.0.0',
  useMode: () => 'home',
}))

// Mock AIStatusContext
vi.mock('../contexts/AIStatusContext', () => ({
  useAIStatus: () => ({
    available: true,
    loading: false,
    refresh: vi.fn(),
  }),
}))

// Mock API client
vi.mock('../api/client', () => ({
  api: mockApi,
}))

// Mock webauthn lib
vi.mock('../lib/webauthn', () => ({
  prepareRegistrationOptions: vi.fn(),
  serializeRegistrationCredential: vi.fn(),
}))

// Import components after mocks
import AIStatusDisplay from '../components/settings/AIStatusDisplay'
import APIKeySection from '../components/settings/APIKeySection'
import { SettingsGeneral, SettingsPrompts, SettingsSources, SettingsSelectors, SettingsUsers, SettingsDanger } from '../components/settings'
import AIQuotaSection from '../components/settings/AIQuotaSection'
import AIUsageSection from '../components/settings/AIUsageSection'
import SourceItem from '../components/settings/SourceItem'
import SelectorItem from '../components/settings/SelectorItem'
import PromptCard from '../components/settings/PromptCard'
import PasskeyItem from '../components/settings/PasskeyItem'
import SettingsPasskeys from '../components/settings/SettingsPasskeys'
import DangerZoneInfo from '../components/settings/DangerZoneInfo'
import ResetPreviewStep from '../components/settings/ResetPreviewStep'
import ConfirmResetStep from '../components/settings/ConfirmResetStep'
import UserProfileCard from '../components/settings/UserProfileCard'
import UserDeletionModal from '../components/settings/UserDeletionModal'
import { formatDate } from '../components/settings/settingsUtils'

// --- settingsUtils ---

describe('settingsUtils', () => {
  it('formatDate formats a date string', () => {
    const result = formatDate('2026-01-15T00:00:00Z')
    expect(result).toContain('2026')
  })
})

// --- AIStatusDisplay ---

describe('AIStatusDisplay', () => {
  it('shows "Connected" when available', () => {
    render(
      <AIStatusDisplay
        aiStatus={{ available: true, configured: true, valid: true, default_model: 'openai/gpt-4', error: null, error_code: null }}
        models={[{ id: 'openai/gpt-4', name: 'GPT-4' }]}
      />,
    )
    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('shows "Invalid key" when configured but not available', () => {
    render(
      <AIStatusDisplay
        aiStatus={{ available: false, configured: true, valid: false, default_model: '', error: 'Bad key', error_code: 'invalid_key' }}
        models={[]}
      />,
    )
    expect(screen.getByText('Invalid key')).toBeInTheDocument()
    expect(screen.getByText('Bad key')).toBeInTheDocument()
  })

  it('shows "Not configured" when not configured', () => {
    render(<AIStatusDisplay aiStatus={{ available: false, configured: false, valid: false, default_model: '', error: null, error_code: null }} models={[]} />)
    expect(screen.getByText('Not configured')).toBeInTheDocument()
  })

  it('shows default model name when available', () => {
    render(
      <AIStatusDisplay
        aiStatus={{ available: true, configured: true, valid: true, default_model: 'openai/gpt-4', error: null, error_code: null }}
        models={[{ id: 'openai/gpt-4', name: 'GPT-4' }]}
      />,
    )
    expect(screen.getByText('GPT-4')).toBeInTheDocument()
  })

  it('falls back to model ID if name not found', () => {
    render(
      <AIStatusDisplay
        aiStatus={{ available: true, configured: true, valid: true, default_model: 'unknown-model', error: null, error_code: null }}
        models={[]}
      />,
    )
    expect(screen.getByText('unknown-model')).toBeInTheDocument()
  })

  it('handles null aiStatus', () => {
    render(<AIStatusDisplay aiStatus={null} models={[]} />)
    expect(screen.getByText('Not configured')).toBeInTheDocument()
  })
})

// --- APIKeySection ---

describe('APIKeySection', () => {
  const defaultProps = {
    aiStatus: { available: false, configured: false, valid: false, default_model: '', error: null, error_code: null } as const,
    models: [] as { id: string; name: string }[],
    onAIStatusChange: vi.fn(),
    onModelsChange: vi.fn(),
  }

  beforeEach(() => vi.clearAllMocks())

  it('renders API key input and buttons', () => {
    render(<APIKeySection {...defaultProps} />)
    expect(screen.getByText('OpenRouter API')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-or-v1-...')).toBeInTheDocument()
    expect(screen.getByText('Test Key')).toBeInTheDocument()
    expect(screen.getByText('Save Key')).toBeInTheDocument()
  })

  it('shows "Update API Key" label when API is available', () => {
    render(
      <APIKeySection
        {...defaultProps}
        aiStatus={{ available: true, configured: true, valid: true, default_model: 'gpt-4', error: null, error_code: null }}
      />,
    )
    expect(screen.getByText('Update API Key')).toBeInTheDocument()
  })

  it('buttons are disabled when input is empty', () => {
    render(<APIKeySection {...defaultProps} />)
    expect(screen.getByText('Test Key').closest('button')).toBeDisabled()
    expect(screen.getByText('Save Key').closest('button')).toBeDisabled()
  })

  it('enables buttons when key is typed', () => {
    render(<APIKeySection {...defaultProps} />)
    fireEvent.change(screen.getByPlaceholderText('sk-or-v1-...'), { target: { value: 'sk-test-123' } })
    expect(screen.getByText('Test Key').closest('button')).not.toBeDisabled()
    expect(screen.getByText('Save Key').closest('button')).not.toBeDisabled()
  })

  it('test key calls API and shows result', async () => {
    render(<APIKeySection {...defaultProps} />)
    fireEvent.change(screen.getByPlaceholderText('sk-or-v1-...'), { target: { value: 'sk-test-123' } })

    await act(async () => {
      fireEvent.click(screen.getByText('Test Key'))
    })

    expect(mockApi.ai.testApiKey).toHaveBeenCalled()
  })

  it('save key calls API and refreshes status', async () => {
    render(<APIKeySection {...defaultProps} />)
    fireEvent.change(screen.getByPlaceholderText('sk-or-v1-...'), { target: { value: 'sk-test-123' } })

    await act(async () => {
      fireEvent.click(screen.getByText('Save Key'))
    })

    expect(mockApi.ai.saveApiKey).toHaveBeenCalled()
  })
})

// --- AIQuotaSection ---

describe('AIQuotaSection', () => {
  const quotaData = {
    limits: { remix: 10, remix_suggestions: 5, scale: 20, tips: 15, discover: 10, timer: 30 },
    usage: { remix: 2, remix_suggestions: 1, scale: 5, tips: 3, discover: 2, timer: 10 },
    unlimited: false,
    resets_at: '2026-04-03T00:00:00Z',
  }

  beforeEach(() => vi.clearAllMocks())

  it('returns null when quotaData is null', () => {
    const { container } = render(<AIQuotaSection quotaData={null} onSave={vi.fn()} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders all feature inputs with values', () => {
    render(<AIQuotaSection quotaData={quotaData} onSave={vi.fn()} />)
    expect(screen.getByText('AI Daily Limits')).toBeInTheDocument()
    expect(screen.getByText('Remixes')).toBeInTheDocument()
    expect(screen.getByText('Tips')).toBeInTheDocument()
    expect(screen.getByText('Timer Naming')).toBeInTheDocument()
  })

  it('saves limits on button click', async () => {
    const onSave = vi.fn()
    render(<AIQuotaSection quotaData={quotaData} onSave={onSave} />)

    await act(async () => {
      fireEvent.click(screen.getByText('Save Limits'))
    })

    expect(mockApi.ai.quotas.update).toHaveBeenCalled()
  })
})

// --- AIUsageSection ---

describe('AIUsageSection', () => {
  it('returns null when quotaData is null', () => {
    const { container } = render(<AIUsageSection quotaData={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('shows unlimited badge when unlimited', () => {
    render(
      <AIUsageSection
        quotaData={{
          limits: { remix: 10, remix_suggestions: 5, scale: 20, tips: 15, discover: 10, timer: 30 },
          usage: { remix: 0, remix_suggestions: 0, scale: 0, tips: 0, discover: 0, timer: 0 },
          unlimited: true,
          resets_at: '2026-04-03T00:00:00Z',
        }}
      />,
    )
    expect(screen.getByText('Unlimited')).toBeInTheDocument()
    expect(screen.getByText('This profile has unlimited AI usage.')).toBeInTheDocument()
  })

  it('shows usage breakdown when not unlimited', () => {
    render(
      <AIUsageSection
        quotaData={{
          limits: { remix: 10, remix_suggestions: 5, scale: 20, tips: 15, discover: 10, timer: 30 },
          usage: { remix: 2, remix_suggestions: 1, scale: 5, tips: 3, discover: 2, timer: 10 },
          unlimited: false,
          resets_at: '2026-04-03T00:00:00Z',
        }}
      />,
    )
    // Usage is rendered as "usage/limit" inside a span
    expect(screen.getByText('Remixes:')).toBeInTheDocument()
    expect(screen.getByText('Resets at', { exact: false })).toBeInTheDocument()
  })
})

// --- SettingsGeneral ---

describe('SettingsGeneral', () => {
  const defaultProps = {
    aiStatus: null,
    models: [] as { id: string; name: string }[],
    onAIStatusChange: vi.fn(),
    onModelsChange: vi.fn(),
    isAdmin: false,
    quotaData: null,
    onQuotaSave: vi.fn(),
  }

  it('renders theme toggle and about section', () => {
    render(<SettingsGeneral {...defaultProps} />)
    expect(screen.getByText('Preferences')).toBeInTheDocument()
    expect(screen.getByText('Light')).toBeInTheDocument()
    expect(screen.getByText('Dark')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
    expect(screen.getByText('1.0.0')).toBeInTheDocument()
  })

  it('hides API key section for non-admin', () => {
    render(<SettingsGeneral {...defaultProps} />)
    expect(screen.queryByText('OpenRouter API')).not.toBeInTheDocument()
  })

  it('shows API key section for admin', () => {
    render(<SettingsGeneral {...defaultProps} isAdmin={true} />)
    expect(screen.getByText('OpenRouter API')).toBeInTheDocument()
  })

  it('clicking Dark calls toggleTheme', () => {
    render(<SettingsGeneral {...defaultProps} />)
    fireEvent.click(screen.getByText('Dark'))
    expect(mockToggleTheme).toHaveBeenCalled()
  })
})

// --- SourceItem ---

describe('SourceItem', () => {
  const enabledSource = {
    id: 1,
    host: 'example.com',
    name: 'Example',
    is_enabled: true,
    search_url_template: '',
    result_selector: '.recipe',
    logo_url: '',
    last_validated_at: null,
    consecutive_failures: 0,
    needs_attention: false,
  }

  it('shows source name and Active badge when enabled', () => {
    render(<SourceItem source={enabledSource} toggling={false} onToggle={vi.fn()} />)
    expect(screen.getByText('Example')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('hides Active badge when disabled', () => {
    render(<SourceItem source={{ ...enabledSource, is_enabled: false }} toggling={false} onToggle={vi.fn()} />)
    expect(screen.queryByText('Active')).not.toBeInTheDocument()
  })

  it('calls onToggle when button clicked', () => {
    const onToggle = vi.fn()
    render(<SourceItem source={enabledSource} toggling={false} onToggle={onToggle} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledWith(1)
  })

  it('disables button when toggling', () => {
    render(<SourceItem source={enabledSource} toggling={true} onToggle={vi.fn()} />)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})

// --- SettingsSources ---

describe('SettingsSources', () => {
  const sources = [
    { id: 1, host: 'a.com', name: 'Source A', is_enabled: true, search_url_template: '', result_selector: '.r', logo_url: '', last_validated_at: null, consecutive_failures: 0, needs_attention: false },
    { id: 2, host: 'b.com', name: 'Source B', is_enabled: false, search_url_template: '', result_selector: '.r', logo_url: '', last_validated_at: null, consecutive_failures: 0, needs_attention: false },
  ]

  it('shows source count', () => {
    render(<SettingsSources sources={sources} onSourcesChange={vi.fn()} />)
    expect(screen.getByText('1 of 2 sources currently enabled')).toBeInTheDocument()
  })

  it('has Enable All and Disable All buttons', () => {
    render(<SettingsSources sources={sources} onSourcesChange={vi.fn()} />)
    expect(screen.getByText('Enable All')).toBeInTheDocument()
    expect(screen.getByText('Disable All')).toBeInTheDocument()
  })

  it('renders each source', () => {
    render(<SettingsSources sources={sources} onSourcesChange={vi.fn()} />)
    expect(screen.getByText('Source A')).toBeInTheDocument()
    expect(screen.getByText('Source B')).toBeInTheDocument()
  })
})

// --- SelectorItem ---

describe('SelectorItem', () => {
  const source = {
    id: 1,
    host: 'example.com',
    name: 'Example',
    is_enabled: true,
    search_url_template: '',
    result_selector: '.recipe-card',
    logo_url: '',
    last_validated_at: '2026-03-30T10:00:00Z',
    consecutive_failures: 0,
    needs_attention: false,
  }

  beforeEach(() => vi.clearAllMocks())

  it('shows source name and current selector', () => {
    render(<SelectorItem source={source} testingAll={false} onSourcesChange={vi.fn()} sources={[source]} />)
    expect(screen.getByText('Example')).toBeInTheDocument()
    expect(screen.getByText('.recipe-card')).toBeInTheDocument()
  })

  it('enters edit mode on Edit click', () => {
    render(<SelectorItem source={source} testingAll={false} onSourcesChange={vi.fn()} sources={[source]} />)
    fireEvent.click(screen.getByText('Edit'))
    expect(screen.getByDisplayValue('.recipe-card')).toBeInTheDocument()
    expect(screen.getByText('Save')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('cancels editing', () => {
    render(<SelectorItem source={source} testingAll={false} onSourcesChange={vi.fn()} sources={[source]} />)
    fireEvent.click(screen.getByText('Edit'))
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByText('Save')).not.toBeInTheDocument()
  })

  it('saves selector changes', async () => {
    const onSourcesChange = vi.fn()
    render(<SelectorItem source={source} testingAll={false} onSourcesChange={onSourcesChange} sources={[source]} />)
    fireEvent.click(screen.getByText('Edit'))
    fireEvent.change(screen.getByDisplayValue('.recipe-card'), { target: { value: '.new-selector' } })

    await act(async () => {
      fireEvent.click(screen.getByText('Save'))
    })

    expect(mockApi.sources.updateSelector).toHaveBeenCalledWith(1, '.new-selector')
  })

  it('tests a source', async () => {
    render(<SelectorItem source={source} testingAll={false} onSourcesChange={vi.fn()} sources={[source]} />)

    await act(async () => {
      fireEvent.click(screen.getByText('Test'))
    })

    expect(mockApi.sources.test).toHaveBeenCalledWith(1)
  })

  it('shows failure count for broken source', () => {
    const broken = { ...source, consecutive_failures: 5, needs_attention: true }
    render(<SelectorItem source={broken} testingAll={false} onSourcesChange={vi.fn()} sources={[broken]} />)
    expect(screen.getByText('Failed 5 times - auto-disabled')).toBeInTheDocument()
  })

  it('shows "(none)" when selector is empty', () => {
    const noSelector = { ...source, result_selector: '' }
    render(<SelectorItem source={noSelector} testingAll={false} onSourcesChange={vi.fn()} sources={[noSelector]} />)
    expect(screen.getByText('(none)')).toBeInTheDocument()
  })
})

// --- SettingsSelectors ---

describe('SettingsSelectors', () => {
  it('renders header and Test All button', () => {
    render(<SettingsSelectors sources={[]} onSourcesChange={vi.fn()} />)
    expect(screen.getByText('Search Source Selector Management')).toBeInTheDocument()
    expect(screen.getByText('Test All Sources')).toBeInTheDocument()
  })
})

// --- PromptCard ---

describe('PromptCard', () => {
  const prompt = {
    prompt_type: 'recipe_remix',
    name: 'Recipe Remix',
    description: 'Generate recipe variations',
    system_prompt: 'You are a chef',
    user_prompt_template: 'Remix {recipe}',
    model: 'openai/gpt-4',
    is_active: true,
  }
  const models = [{ id: 'openai/gpt-4', name: 'GPT-4' }]

  beforeEach(() => vi.clearAllMocks())

  it('shows prompt name, description, and model', () => {
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={vi.fn()} />)
    expect(screen.getByText('Recipe Remix')).toBeInTheDocument()
    expect(screen.getByText('Generate recipe variations')).toBeInTheDocument()
    expect(screen.getByText('GPT-4')).toBeInTheDocument()
  })

  it('shows Disabled badge when inactive', () => {
    render(<PromptCard prompt={{ ...prompt, is_active: false }} models={models} onPromptUpdated={vi.fn()} />)
    expect(screen.getByText('Disabled')).toBeInTheDocument()
  })

  it('expands to show read-only prompts', () => {
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={vi.fn()} />)
    fireEvent.click(screen.getByLabelText('Expand'))
    expect(screen.getByText('You are a chef')).toBeInTheDocument()
    expect(screen.getByText('Remix {recipe}')).toBeInTheDocument()
  })

  it('collapses expanded view', () => {
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={vi.fn()} />)
    fireEvent.click(screen.getByLabelText('Expand'))
    expect(screen.getByText('You are a chef')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Collapse'))
    expect(screen.queryByText('You are a chef')).not.toBeInTheDocument()
  })

  it('enters edit mode and shows form', () => {
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={vi.fn()} />)
    fireEvent.click(screen.getByText('Edit'))
    expect(screen.getByDisplayValue('You are a chef')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Remix {recipe}')).toBeInTheDocument()
    expect(screen.getByText('Save Changes')).toBeInTheDocument()
  })

  it('cancels edit mode', () => {
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={vi.fn()} />)
    fireEvent.click(screen.getByText('Edit'))
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByText('Save Changes')).not.toBeInTheDocument()
  })

  it('saves prompt changes', async () => {
    const onPromptUpdated = vi.fn()
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={onPromptUpdated} />)
    fireEvent.click(screen.getByText('Edit'))
    fireEvent.change(screen.getByDisplayValue('You are a chef'), { target: { value: 'You are a baker' } })

    await act(async () => {
      fireEvent.click(screen.getByText('Save Changes'))
    })

    expect(mockApi.ai.prompts.update).toHaveBeenCalledWith('recipe_remix', expect.objectContaining({ system_prompt: 'You are a baker' }))
    await waitFor(() => expect(onPromptUpdated).toHaveBeenCalled())
  })

  it('toggles active/disabled status in edit mode', () => {
    render(<PromptCard prompt={prompt} models={models} onPromptUpdated={vi.fn()} />)
    fireEvent.click(screen.getByText('Edit'))
    // The status button shows Active since prompt.is_active is true
    const activeBtn = screen.getByText('Active')
    fireEvent.click(activeBtn)
    // Now it should show Disabled
    expect(screen.getByText('Disabled')).toBeInTheDocument()
  })
})

// --- SettingsPrompts ---

describe('SettingsPrompts', () => {
  const prompts = [
    {
      prompt_type: 'recipe_remix',
      name: 'Recipe Remix',
      description: 'Remix desc',
      system_prompt: 'sys',
      user_prompt_template: 'user',
      model: 'openai/gpt-4',
      is_active: true,
    },
  ]

  it('shows AI prompts info', () => {
    render(<SettingsPrompts aiStatus={{ available: true, configured: true, valid: true, default_model: '', error: null, error_code: null }} prompts={prompts} models={[]} onPromptsChange={vi.fn()} />)
    expect(screen.getByText('AI Prompts Configuration')).toBeInTheDocument()
  })

  it('shows warning when AI is unavailable', () => {
    render(<SettingsPrompts aiStatus={{ available: false, configured: false, valid: false, default_model: '', error: null, error_code: null }} prompts={[]} models={[]} onPromptsChange={vi.fn()} />)
    expect(screen.getByText(/Configure your OpenRouter API key/)).toBeInTheDocument()
  })

  it('renders prompt cards', () => {
    render(<SettingsPrompts aiStatus={{ available: true, configured: true, valid: true, default_model: '', error: null, error_code: null }} prompts={prompts} models={[]} onPromptsChange={vi.fn()} />)
    expect(screen.getByText('Recipe Remix')).toBeInTheDocument()
  })
})

// --- PasskeyItem ---

describe('PasskeyItem', () => {
  it('renders passkey info', () => {
    render(<PasskeyItem id={1} createdAt="2026-01-01T00:00:00Z" lastUsedAt="2026-03-01T00:00:00Z" isDeletable={true} onDelete={vi.fn()} />)
    expect(screen.getByText('Passkey #1')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('hides delete button when not deletable', () => {
    render(<PasskeyItem id={2} createdAt={null} lastUsedAt={null} isDeletable={false} onDelete={vi.fn()} />)
    expect(screen.queryByText('Delete')).not.toBeInTheDocument()
  })

  it('shows "Never" for null dates', () => {
    render(<PasskeyItem id={3} createdAt={null} lastUsedAt={null} isDeletable={false} onDelete={vi.fn()} />)
    expect(screen.getByText('Added Never')).toBeInTheDocument()
    expect(screen.getByText('Last used: Never')).toBeInTheDocument()
  })

  it('calls onDelete with id', () => {
    const onDelete = vi.fn()
    render(<PasskeyItem id={5} createdAt="2026-01-01T00:00:00Z" lastUsedAt={null} isDeletable={true} onDelete={onDelete} />)
    fireEvent.click(screen.getByText('Delete'))
    expect(onDelete).toHaveBeenCalledWith(5)
  })
})

// --- SettingsPasskeys ---

describe('SettingsPasskeys', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows loading state initially', () => {
    mockApi.passkey.listCredentials.mockReturnValueOnce(new Promise(() => {}))
    render(<SettingsPasskeys />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders credentials after loading', async () => {
    render(<SettingsPasskeys />)
    await waitFor(() => {
      expect(screen.getByText('Passkey #1')).toBeInTheDocument()
      expect(screen.getByText('Passkey #2')).toBeInTheDocument()
    })
    expect(screen.getByText('2 passkeys registered')).toBeInTheDocument()
  })

  it('shows Add Passkey button', async () => {
    render(<SettingsPasskeys />)
    await waitFor(() => {
      expect(screen.getByText('Add Passkey')).toBeInTheDocument()
    })
  })
})

// --- DangerZoneInfo ---

describe('DangerZoneInfo', () => {
  it('renders danger zone content', () => {
    render(<DangerZoneInfo onResetClick={vi.fn()} />)
    expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reset Database' })).toBeInTheDocument()
  })

  it('calls onResetClick when button clicked', () => {
    const onResetClick = vi.fn()
    render(<DangerZoneInfo onResetClick={onResetClick} />)
    fireEvent.click(screen.getByRole('button', { name: 'Reset Database' }))
    expect(onResetClick).toHaveBeenCalled()
  })
})

// --- ResetPreviewStep ---

describe('ResetPreviewStep', () => {
  const preview = {
    data_counts: {
      profiles: 2,
      recipes: 10,
      recipe_images: 5,
      favorites: 8,
      collections: 3,
      view_history: 20,
      ai_suggestions: 4,
      serving_adjustments: 2,
    },
  }

  it('shows data counts', () => {
    render(<ResetPreviewStep resetPreview={preview} onCancel={vi.fn()} onContinue={vi.fn()} />)
    expect(screen.getByText('Reset Database?')).toBeInTheDocument()
    expect(screen.getByText(/2 profiles/)).toBeInTheDocument()
    expect(screen.getByText(/10 recipes/)).toBeInTheDocument()
  })

  it('calls onContinue when clicked', () => {
    const onContinue = vi.fn()
    render(<ResetPreviewStep resetPreview={preview} onCancel={vi.fn()} onContinue={onContinue} />)
    fireEvent.click(screen.getByText('I understand, continue'))
    expect(onContinue).toHaveBeenCalled()
  })

  it('calls onCancel when clicked', () => {
    const onCancel = vi.fn()
    render(<ResetPreviewStep resetPreview={preview} onCancel={onCancel} onContinue={vi.fn()} />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(onCancel).toHaveBeenCalled()
  })
})

// --- ConfirmResetStep ---

describe('ConfirmResetStep', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders confirm input and disabled button', () => {
    render(<ConfirmResetStep onBack={vi.fn()} />)
    expect(screen.getByText('Confirm Reset')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Type RESET')).toBeInTheDocument()
    // Reset button should be disabled
    const resetBtn = screen.getByRole('button', { name: /Reset Database/i })
    expect(resetBtn).toBeDisabled()
  })

  it('enables button when RESET is typed', () => {
    render(<ConfirmResetStep onBack={vi.fn()} />)
    fireEvent.change(screen.getByPlaceholderText('Type RESET'), { target: { value: 'RESET' } })
    const resetBtn = screen.getByRole('button', { name: /Reset Database/i })
    expect(resetBtn).not.toBeDisabled()
  })

  it('calls onBack when Back clicked', () => {
    const onBack = vi.fn()
    render(<ConfirmResetStep onBack={onBack} />)
    fireEvent.click(screen.getByText('Back'))
    expect(onBack).toHaveBeenCalled()
  })

  it('calls api.system.reset when confirmed', async () => {
    // Mock window.location
    const originalLocation = window.location
    Object.defineProperty(window, 'location', { value: { href: '' }, writable: true })

    render(<ConfirmResetStep onBack={vi.fn()} />)
    fireEvent.change(screen.getByPlaceholderText('Type RESET'), { target: { value: 'RESET' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Reset Database/i }))
    })

    expect(mockApi.system.reset).toHaveBeenCalledWith('RESET')

    Object.defineProperty(window, 'location', { value: originalLocation, writable: true })
  })
})

// --- SettingsDanger ---

describe('SettingsDanger', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders DangerZoneInfo', () => {
    render(<SettingsDanger />)
    expect(screen.getByText('Danger Zone')).toBeInTheDocument()
  })

  it('opens reset modal on button click', async () => {
    render(<SettingsDanger />)

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Reset Database' }))
    })

    await waitFor(() => {
      expect(screen.getByText('Reset Database?')).toBeInTheDocument()
    })
  })
})

// --- UserProfileCard ---

describe('UserProfileCard', () => {
  const profile = {
    id: 2,
    name: 'Alice',
    avatar_color: '#f00',
    theme: 'light',
    unit_preference: 'metric',
    unlimited_ai: false,
    created_at: '2026-01-01T00:00:00Z',
    stats: { favorites: 5, collections: 2, collection_items: 4, remixes: 3, view_history: 10, scaling_cache: 0, discover_cache: 0 },
  }

  it('renders profile info', () => {
    render(<UserProfileCard profile={profile} isCurrent={false} onDeleteClick={vi.fn()} onProfileUpdate={vi.fn()} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText(/5 favorites/)).toBeInTheDocument()
    expect(screen.getByText(/2 collections/)).toBeInTheDocument()
  })

  it('shows Current badge for current profile', () => {
    render(<UserProfileCard profile={profile} isCurrent={true} onDeleteClick={vi.fn()} onProfileUpdate={vi.fn()} />)
    expect(screen.getByText('Current')).toBeInTheDocument()
  })

  it('disables delete for current profile', () => {
    render(<UserProfileCard profile={profile} isCurrent={true} onDeleteClick={vi.fn()} onProfileUpdate={vi.fn()} />)
    const deleteBtn = screen.getByTitle('Cannot delete current profile')
    expect(deleteBtn).toBeDisabled()
  })

  it('calls onDeleteClick for non-current profile', () => {
    const onDeleteClick = vi.fn()
    render(<UserProfileCard profile={profile} isCurrent={false} onDeleteClick={onDeleteClick} onProfileUpdate={vi.fn()} />)
    fireEvent.click(screen.getByTitle('Delete profile'))
    expect(onDeleteClick).toHaveBeenCalledWith(2)
  })

  it('enters rename mode on pencil click', () => {
    render(<UserProfileCard profile={profile} isCurrent={false} onDeleteClick={vi.fn()} onProfileUpdate={vi.fn()} />)
    fireEvent.click(screen.getByTitle('Rename'))
    expect(screen.getByLabelText('Profile name')).toBeInTheDocument()
  })

  it('toggles unlimited AI', async () => {
    const onProfileUpdate = vi.fn()
    render(<UserProfileCard profile={profile} isCurrent={false} onDeleteClick={vi.fn()} onProfileUpdate={onProfileUpdate} />)

    await act(async () => {
      fireEvent.click(screen.getByRole('switch', { name: /Unlimited AI/i }))
    })

    expect(mockApi.profiles.setUnlimited).toHaveBeenCalledWith(2, true)
  })
})

// --- UserDeletionModal ---

describe('UserDeletionModal', () => {
  const preview = {
    profile: { id: 2, name: 'Alice', avatar_color: '#f00', created_at: '2026-01-01T00:00:00Z' },
    data_to_delete: { remixes: 3, remix_images: 1, favorites: 5, collections: 2, collection_items: 4, view_history: 10, scaling_cache: 0, discover_cache: 0 },
  }

  it('renders profile info and deletion summary', () => {
    render(<UserDeletionModal preview={preview} deleting={false} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('Delete Profile?')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText(/3 remixed recipe/)).toBeInTheDocument()
    expect(screen.getByText(/5 favorite/)).toBeInTheDocument()
  })

  it('shows no data message when nothing to delete', () => {
    const emptyPreview = {
      ...preview,
      data_to_delete: { remixes: 0, remix_images: 0, favorites: 0, collections: 0, collection_items: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 },
    }
    render(<UserDeletionModal preview={emptyPreview} deleting={false} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/No associated data/)).toBeInTheDocument()
  })

  it('calls onConfirm and onCancel', () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    render(<UserDeletionModal preview={preview} deleting={false} onConfirm={onConfirm} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('Delete Profile'))
    expect(onConfirm).toHaveBeenCalled()
    fireEvent.click(screen.getByText('Cancel'))
    expect(onCancel).toHaveBeenCalled()
  })

  it('disables delete button when deleting', () => {
    render(<UserDeletionModal preview={preview} deleting={true} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('Delete Profile').closest('button')).toBeDisabled()
  })
})

// --- SettingsUsers ---

describe('SettingsUsers', () => {
  const profiles = [
    {
      id: 1,
      name: 'Me',
      avatar_color: '#000',
      theme: 'light',
      unit_preference: 'metric',
      unlimited_ai: false,
      created_at: '2026-01-01T00:00:00Z',
      stats: { favorites: 0, collections: 0, collection_items: 0, remixes: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 },
    },
    {
      id: 2,
      name: 'Alice',
      avatar_color: '#f00',
      theme: 'light',
      unit_preference: 'metric',
      unlimited_ai: false,
      created_at: '2026-02-01T00:00:00Z',
      stats: { favorites: 5, collections: 2, collection_items: 4, remixes: 3, view_history: 10, scaling_cache: 0, discover_cache: 0 },
    },
  ]

  it('shows profile count and cards', () => {
    render(<SettingsUsers profiles={profiles} currentProfileId={1} onProfilesChange={vi.fn()} />)
    expect(screen.getByText('User Management')).toBeInTheDocument()
    expect(screen.getByText('2 profiles')).toBeInTheDocument()
    expect(screen.getByText('Me')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })

  it('shows singular "profile" for single profile', () => {
    render(<SettingsUsers profiles={[profiles[0]]} currentProfileId={1} onProfilesChange={vi.fn()} />)
    expect(screen.getByText('1 profile')).toBeInTheDocument()
  })
})
