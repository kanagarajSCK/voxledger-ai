import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Modal } from '../../components/ui/Modal'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { useVoiceWebSocket, WebSocketMessage } from '../../hooks/useVoiceWebSocket'
import { useAudioStreamer } from '../../hooks/useAudioStreamer'
import { VoiceLanguage, VoiceState, PendingVoiceAction } from '../../types/voice'
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  CheckCircle2,
  XCircle,
  Sparkles,
  Send,
  Radio,
  AlertCircle,
} from 'lucide-react'

export interface VoiceAssistantModalProps {
  isOpen: boolean
  onClose: () => void
}

const LANGUAGE_OPTIONS: { code: VoiceLanguage; label: string; native: string }[] = [
  { code: 'hi-IN', label: 'Hindi', native: 'हिन्दी' },
  { code: 'en-IN', label: 'English', native: 'English' },
  { code: 'ta-IN', label: 'Tamil', native: 'தமிழ்' },
  { code: 'kn-IN', label: 'Kannada', native: 'ಕನ್ನಡ' },
]

export const VoiceAssistantModal: React.FC<VoiceAssistantModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient()
  const [language, setLanguage] = useState<VoiceLanguage>('hi-IN')
  const [voiceState, setVoiceState] = useState<VoiceState>('idle')
  const [transcript, setTranscript] = useState('')
  const [spokenResponse, setSpokenResponse] = useState<string | null>(null)
  const [pendingAction, setPendingAction] = useState<PendingVoiceAction | null>(null)
  const [executedTx, setExecutedTx] = useState<{ amount: string; type: string; new_balance: string } | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [textCommandInput, setTextCommandInput] = useState('')
  const [audioMuted, setAudioMuted] = useState(false)

  const audioPlayerRef = useRef<HTMLAudioElement | null>(null)

  // 1. Play TTS base64 audio
  const playAudioBase64 = useCallback((base64Wav: string) => {
    if (audioMuted) return
    try {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause()
      }
      const audioUrl = `data:audio/wav;base64,${base64Wav}`
      const audio = new Audio(audioUrl)
      audioPlayerRef.current = audio
      setVoiceState('speaking')
      audio.onended = () => {
        setVoiceState((prev) => (prev === 'speaking' ? 'idle' : prev))
      }
      audio.play().catch(() => {
        setVoiceState((prev) => (prev === 'speaking' ? 'idle' : prev))
      })
    } catch {
      setVoiceState('idle')
    }
  }, [audioMuted])

  // 2. WebSocket message handler
  const handleWsMessage = useCallback((msg: WebSocketMessage) => {
    const type = msg.type as string

    if (type === 'transcript') {
      const text = msg.text as string
      setTranscript(text)
      if (msg.is_final) {
        setVoiceState('transcribing')
      }
    } else if (type === 'speech_start') {
      setVoiceState('listening')
    } else if (type === 'action_proposed') {
      const action = msg.action as PendingVoiceAction
      setPendingAction(action)
      setVoiceState('confirming')
      setSpokenResponse((msg.spoken_prompt as string) || null)
      if (msg.audio_base64) {
        playAudioBase64(msg.audio_base64 as string)
      }
    } else if (type === 'action_executed') {
      const tx = msg.transaction as { amount: string; type: string; new_balance: string }
      setExecutedTx(tx)
      setPendingAction(null)
      setVoiceState('idle')
      setSpokenResponse((msg.spoken_response as string) || null)
      if (msg.audio_base64) {
        playAudioBase64(msg.audio_base64 as string)
      }
      // Refresh dashboard and customer balances
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['customer'] })
    } else if (type === 'action_cancelled') {
      setPendingAction(null)
      setVoiceState('idle')
      setSpokenResponse((msg.spoken_response as string) || 'Cancelled.')
      if (msg.audio_base64) {
        playAudioBase64(msg.audio_base64 as string)
      }
    } else if (type === 'balance_report' || type === 'daily_summary_report') {
      setVoiceState('idle')
      setSpokenResponse((msg.spoken_response as string) || null)
      if (msg.audio_base64) {
        playAudioBase64(msg.audio_base64 as string)
      }
    } else if (type === 'payment_rejected' || type === 'customer_not_found' || type === 'validation_error') {
      setVoiceState('idle')
      setErrorMessage((msg.spoken_response as string) || (msg.message as string) || 'Validation error')
      if (msg.audio_base64) {
        playAudioBase64(msg.audio_base64 as string)
      }
    } else if (type === 'unknown_intent') {
      setVoiceState('idle')
      setSpokenResponse((msg.spoken_response as string) || "Sorry, I didn't understand.")
      if (msg.audio_base64) {
        playAudioBase64(msg.audio_base64 as string)
      }
    }
  }, [playAudioBase64, queryClient])

  // 3. Connect WebSocket
  const { status: wsStatus, connect, disconnect, sendMessage, sendBinary } = useVoiceWebSocket({
    onMessage: handleWsMessage,
  })

  // 4. Audio streamer
  const handleAudioChunk = useCallback((chunk: ArrayBuffer) => {
    sendBinary(chunk)
  }, [sendBinary])

  const { isRecording, volumeLevel, error: micError, startRecording, stopRecording } = useAudioStreamer({
    onAudioChunk: handleAudioChunk,
    sampleRate: 16000,
  })

  // Initialize or teardown when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      connect()
      setTranscript('')
      setPendingAction(null)
      setExecutedTx(null)
      setErrorMessage(null)
      setVoiceState('idle')
    } else {
      stopRecording()
      disconnect()
    }
  }, [isOpen, connect, disconnect, stopRecording])

  // Handle language change
  const handleLanguageChange = (newLang: VoiceLanguage) => {
    setLanguage(newLang)
    sendMessage({ type: 'set_language', language: newLang })
  }

  // Toggle microphone
  const toggleListening = async () => {
    if (isRecording) {
      stopRecording()
      sendMessage({ type: 'stop_stream' })
      setVoiceState('transcribing')
    } else {
      setErrorMessage(null)
      setExecutedTx(null)
      setTranscript('')
      setSpokenResponse(null)
      sendMessage({ type: 'start_stream', language, sample_rate: 16000 })
      await startRecording()
      setVoiceState('listening')
    }
  }

  // Handle typed fallback command
  const handleSendTextCommand = (e: React.FormEvent) => {
    e.preventDefault()
    if (!textCommandInput.trim()) return
    setErrorMessage(null)
    setExecutedTx(null)
    setTranscript(textCommandInput)
    sendMessage({ type: 'text_command', text: textCommandInput.trim(), language })
    setTextCommandInput('')
    setVoiceState('transcribing')
  }

  // Explicit confirmation button
  const handleConfirmAction = () => {
    sendMessage({ type: 'confirm_action' })
  }

  // Explicit cancel button
  const handleCancelAction = () => {
    sendMessage({ type: 'cancel_action' })
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="VoxLedger AI Multilingual Voice Assistant"
      description="Natural Indic voice accounting powered by Gnani Prisma v3.0 & Timbre v3.0"
      className="max-w-2xl"
    >
      <div className="space-y-5">
        {/* Top Controls: Language Switcher, Audio Mute, and WS Status */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700">Language:</span>
            <div className="flex items-center gap-1">
              {LANGUAGE_OPTIONS.map((opt) => (
                <button
                  key={opt.code}
                  onClick={() => handleLanguageChange(opt.code)}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                    language === opt.code
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <span>{opt.native}</span>
                  <span className="ml-1 text-[10px] opacity-80">({opt.label})</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setAudioMuted(!audioMuted)}
              className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 transition-colors"
              title={audioMuted ? 'Unmute Assistant' : 'Mute Assistant'}
            >
              {audioMuted ? <VolumeX className="w-4 h-4 text-red-500" /> : <Volume2 className="w-4 h-4 text-emerald-600" />}
            </button>

            <Badge
              variant={wsStatus === 'connected' ? 'success' : wsStatus === 'connecting' ? 'warning' : 'neutral'}
              className="gap-1 font-mono text-[10px]"
            >
              <Radio className="w-3 h-3 animate-pulse" />
              {(wsStatus || 'connected').toUpperCase()}
            </Badge>
          </div>
        </div>

        {/* Center: Microphone & Soundwave Visualizer */}
        <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-b from-slate-900 to-slate-950 rounded-2xl text-white shadow-xl relative overflow-hidden">
          {/* Subtle background glow */}
          <div
            className={`absolute w-72 h-72 rounded-full blur-3xl transition-opacity duration-500 ${
              isRecording ? 'bg-emerald-500/20 opacity-100' : 'bg-transparent opacity-0'
            }`}
          />

          {/* Microphone Button with Dynamic Soundwave Halo */}
          <div className="relative mb-4">
            {isRecording && (
              <div
                className="absolute inset-0 rounded-full bg-emerald-500 animate-ping opacity-30 pointer-events-none"
                style={{ transform: `scale(${1 + volumeLevel * 0.8})` }}
              />
            )}
            <button
              onClick={toggleListening}
              aria-label={isRecording ? 'Stop voice recording' : 'Start voice recording'}
              className={`relative z-10 w-20 h-20 sm:w-24 sm:h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg ${
                isRecording
                  ? 'bg-red-600 hover:bg-red-700 text-white ring-4 ring-red-400/40 scale-105'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white ring-4 ring-emerald-500/30'
              }`}
            >
              {isRecording ? <MicOff className="w-9 h-9" /> : <Mic className="w-9 h-9" />}
            </button>
          </div>

          {/* Voice State Status Indicator */}
          <div className="text-center space-y-1 z-10">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-semibold text-emerald-400">
              <Sparkles className="w-3.5 h-3.5" />
              {voiceState === 'listening' && 'Listening... Speak now'}
              {voiceState === 'transcribing' && 'Processing with Prisma v3.0...'}
              {voiceState === 'confirming' && 'Awaiting Confirmation'}
              {voiceState === 'speaking' && 'Assistant Speaking (Timbre v3.0)...'}
              {voiceState === 'idle' && (isRecording ? 'Listening...' : 'Tap Mic to Start Speaking')}
            </div>

            <p className="text-xs text-slate-400 max-w-sm pt-1">
              Try: <span className="text-slate-200">"Ramesh-ku 340 rupees udhaar podu"</span> or{' '}
              <span className="text-slate-200">"Ramesh paid 200 rupees"</span>
            </p>
          </div>

          {/* Sound Wave Animation Bars */}
          {isRecording && (
            <div className="flex items-center gap-1 h-6 mt-4 z-10">
              {[0.4, 0.7, 1.0, 0.6, 0.8, 0.5, 0.9, 0.7, 0.4].map((scale, i) => (
                <div
                  key={i}
                  className="w-1 bg-emerald-400 rounded-full transition-all duration-75"
                  style={{
                    height: `${Math.max(4, volumeLevel * 24 * scale)}px`,
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Live Transcription Banner */}
        {transcript && (
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Live Speech Transcript
            </div>
            <p className="text-sm font-medium text-slate-800 italic">"{transcript}"</p>
          </div>
        )}

        {/* Error Alert */}
        {(errorMessage || micError) && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Notice</p>
              <p>{errorMessage || micError}</p>
            </div>
          </div>
        )}

        {/* Pending Action Confirmation Card (Safety Barrier) */}
        {pendingAction && (
          <div className="p-4 rounded-xl border-2 border-amber-300 bg-amber-50/80 space-y-3 shadow-md animate-in fade-in duration-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                Action Verification Required (पुष्टिकरण)
              </span>
              <span
                className={`text-xs font-extrabold px-2 py-0.5 rounded ${
                  pendingAction.type === 'CREDIT' ? 'bg-red-100 text-red-800' : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {pendingAction.type === 'CREDIT' ? '+ CREDIT GIVEN (उधार)' : '- PAYMENT RECEIVED (जमा)'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-white p-3 rounded-lg border border-amber-200">
              <div>
                <span className="text-slate-500">Customer</span>
                <p className="text-sm font-bold text-slate-900">{pendingAction.customer_name}</p>
              </div>
              <div>
                <span className="text-slate-500">Amount</span>
                <p
                  className={`text-base font-extrabold ${
                    pendingAction.type === 'CREDIT' ? 'text-red-600' : 'text-emerald-600'
                  }`}
                >
                  ₹{parseFloat(pendingAction.amount).toFixed(2)}
                </p>
              </div>
              <div>
                <span className="text-slate-500">Current Balance</span>
                <p className="font-semibold text-slate-800">₹{parseFloat(pendingAction.current_balance).toFixed(2)}</p>
              </div>
              <div>
                <span className="text-slate-500">Projected Balance</span>
                <p className="font-bold text-slate-900">₹{parseFloat(pendingAction.projected_balance).toFixed(2)}</p>
              </div>
            </div>

            {spokenResponse && (
              <p className="text-xs text-amber-950 font-medium bg-amber-100/60 p-2 rounded border border-amber-200">
                💬 Assistant: "{spokenResponse}"
              </p>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={handleCancelAction} className="gap-1 text-slate-700">
                <XCircle className="w-4 h-4 text-slate-500" />
                Cancel (रद्द करें)
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmAction}
                className="gap-1.5 bg-emerald-600 hover:bg-emerald-700"
              >
                <CheckCircle2 className="w-4 h-4" />
                Confirm & Record (पुष्टि करें)
              </Button>
            </div>
          </div>
        )}

        {/* Executed Success Card */}
        {executedTx && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-xs text-emerald-950 animate-in fade-in">
            <div className="flex items-center gap-1.5 font-bold text-emerald-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Transaction Recorded Successfully!</span>
            </div>
            <p>
              {executedTx.type === 'CREDIT' ? 'Credit of ' : 'Payment of '}
              <span className="font-bold">₹{parseFloat(executedTx.amount).toFixed(2)}</span> has been updated in the
              digital ledger. New balance: <span className="font-bold">₹{parseFloat(executedTx.new_balance).toFixed(2)}</span>.
            </p>
          </div>
        )}

        {/* Assistant Spoken Response Text */}
        {spokenResponse && !pendingAction && (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
            <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">Assistant Response</span>
            <p className="text-sm font-medium text-slate-800">"{spokenResponse}"</p>
          </div>
        )}

        {/* Text Command Fallback Bar */}
        <form onSubmit={handleSendTextCommand} className="flex items-center gap-2 pt-2 border-t border-slate-100">
          <input
            type="text"
            placeholder="Or type voice command (e.g. Ramesh paid 200)..."
            value={textCommandInput}
            onChange={(e) => setTextCommandInput(e.target.value)}
            className="flex-1 h-10 px-3.5 rounded-lg border border-slate-300 text-xs text-slate-900 outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <Button type="submit" variant="primary" size="sm" className="gap-1.5 h-10">
            <Send className="w-3.5 h-3.5" />
            Send
          </Button>
        </form>
      </div>
    </Modal>
  )
}
