import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Layers, BookOpen, Mic } from 'lucide-react'
import { useVoiceAssistant } from '../features/voice/VoiceContext'
import { cn } from '../lib/utils'

export const MobileNav: React.FC = () => {
  const location = useLocation()
  const { openVoiceModal } = useVoiceAssistant()

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-slate-200 px-3 py-1.5 flex items-center justify-between shadow-lg pb-[max(0.5rem,env(safe-area-inset-bottom))]">
      {/* Dashboard */}
      <Link
        to="/"
        className={cn(
          'flex flex-col items-center gap-1 text-[10px] font-medium touch-target justify-center transition-colors min-w-[56px]',
          location.pathname === '/' ? 'text-emerald-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
        )}
      >
        <LayoutDashboard className="w-5 h-5" />
        <span>Dashboard</span>
      </Link>

      {/* Customers */}
      <Link
        to="/customers"
        className={cn(
          'flex flex-col items-center gap-1 text-[10px] font-medium touch-target justify-center transition-colors min-w-[56px]',
          location.pathname.startsWith('/customers') ? 'text-emerald-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
        )}
      >
        <Users className="w-5 h-5" />
        <span>Customers</span>
      </Link>

      {/* Central Raised Voice Mic Button */}
      <div className="-mt-5 flex flex-col items-center">
        <button
          onClick={openVoiceModal}
          aria-label="Open Voice Assistant"
          className="w-12 h-12 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center shadow-lg shadow-emerald-600/40 hover:scale-105 active:scale-95 transition-all border-2 border-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <Mic className="w-6 h-6 animate-pulse" />
        </button>
        <span className="text-[9px] font-bold text-emerald-700 mt-0.5">बोलें</span>
      </div>

      {/* Architecture */}
      <Link
        to="/foundation"
        className={cn(
          'flex flex-col items-center gap-1 text-[10px] font-medium touch-target justify-center transition-colors min-w-[56px]',
          location.pathname.startsWith('/foundation') ? 'text-emerald-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
        )}
      >
        <Layers className="w-5 h-5" />
        <span>Arch</span>
      </Link>

      {/* API Docs */}
      <a
        href="http://localhost:8000/docs"
        target="_blank"
        rel="noreferrer"
        className="flex flex-col items-center gap-1 text-[10px] font-medium text-slate-500 hover:text-emerald-600 touch-target justify-center min-w-[56px]"
      >
        <BookOpen className="w-5 h-5" />
        <span>Docs</span>
      </a>
    </nav>
  )
}
