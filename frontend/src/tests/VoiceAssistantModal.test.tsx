import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { VoiceAssistantModal } from '../features/voice/VoiceAssistantModal'

// Mock useVoiceWebSocket hook
const mockSendBinary = vi.fn()
const mockSendMessage = vi.fn()

vi.mock('../hooks/useVoiceWebSocket', () => ({
  useVoiceWebSocket: () => {
    return {
      status: 'connected',
      isConnected: true,
      lastMessage: null,
      sendMessage: mockSendMessage,
      sendBinary: mockSendBinary,
      connect: vi.fn(),
      disconnect: vi.fn(),
    }
  },
}))

// Mock useAudioStreamer hook
const mockStartAudio = vi.fn().mockResolvedValue(true)
const mockStopAudio = vi.fn()

vi.mock('../hooks/useAudioStreamer', () => ({
  useAudioStreamer: () => ({
    isStreaming: false,
    audioLevel: 0,
    permissionError: null,
    startStreaming: mockStartAudio,
    stopStreaming: mockStopAudio,
  }),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('VoiceAssistantModal Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders voice assistant modal with title, status, and language choices', () => {
    render(<VoiceAssistantModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    expect(screen.getByText(/Multilingual Voice Assistant/i)).toBeInTheDocument()
    expect(screen.getByText(/Gnani Prisma v3\.0 & Timbre v3\.0/i)).toBeInTheDocument()

    // 4 Indic languages
    expect(screen.getByRole('button', { name: /हिन्दी/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /English/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /தமிழ்/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ಕನ್ನಡ/i })).toBeInTheDocument()
  })

  it('allows switching voice language', () => {
    render(<VoiceAssistantModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    const tamilBtn = screen.getByRole('button', { name: /தமிழ்/i })
    fireEvent.click(tamilBtn)

    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'set_language',
      language: 'ta-IN',
    })
  })

  it('renders microphone button and typed command fallback input', () => {
    render(<VoiceAssistantModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    // Microphone toggle button
    expect(screen.getByRole('button', { name: /Start voice recording/i })).toBeInTheDocument()

    // Fallback typed command input
    const input = screen.getByPlaceholderText(/Or type voice command/i)
    expect(input).toBeInTheDocument()

    // Send button
    expect(screen.getByRole('button', { name: /Send/i })).toBeInTheDocument()
  })

  it('sends text command when typing and submitting fallback form', () => {
    render(<VoiceAssistantModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    const input = screen.getByPlaceholderText(/Or type voice command/i)
    fireEvent.change(input, { target: { value: 'Ramesh 340 udhaar' } })

    const sendBtn = screen.getByRole('button', { name: /Send/i })
    fireEvent.click(sendBtn)

    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'text_command',
      text: 'Ramesh 340 udhaar',
      language: 'hi-IN',
    })
  })

  it('renders audio mute toggle button and toggles state', () => {
    render(<VoiceAssistantModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    const muteBtn = screen.getByTitle('Mute Assistant')
    expect(muteBtn).toBeInTheDocument()

    fireEvent.click(muteBtn)
    expect(screen.getByTitle('Unmute Assistant')).toBeInTheDocument()
  })
})
