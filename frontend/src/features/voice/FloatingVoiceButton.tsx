import React from 'react'
import { Mic, Sparkles } from 'lucide-react'
import { useVoiceAssistant } from './VoiceContext'

export const FloatingVoiceButton: React.FC = () => {
  const { openVoiceModal } = useVoiceAssistant()

  return (
    <div className="fixed bottom-20 right-4 sm:bottom-6 sm:right-6 z-40">
      <button
        onClick={openVoiceModal}
        aria-label="Open Voice Assistant (बोलकर खाता लिखें)"
        className="group relative flex items-center gap-2.5 px-4 py-3 sm:px-5 sm:py-3.5 rounded-full bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 text-white shadow-xl shadow-emerald-600/30 hover:shadow-emerald-600/50 hover:scale-105 active:scale-95 transition-all duration-200 border border-emerald-400/30 focus:outline-none focus:ring-4 focus:ring-emerald-500/40"
      >
        {/* Pulsing ring */}
        <span className="absolute -inset-0.5 rounded-full bg-emerald-400 opacity-30 group-hover:opacity-70 blur-sm animate-pulse" />

        <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-white/20">
          <Mic className="w-5 h-5 text-white animate-bounce-slow" />
        </div>

        <div className="relative flex flex-col items-start text-left">
          <div className="flex items-center gap-1">
            <span className="text-xs sm:text-sm font-bold tracking-tight">Voice Khata</span>
            <Sparkles className="w-3 h-3 text-emerald-200" />
          </div>
          <span className="text-[10px] text-emerald-100 hidden sm:inline">
            बोलकर एंट्री करें • Voice AI
          </span>
        </div>
      </button>
    </div>
  )
}
