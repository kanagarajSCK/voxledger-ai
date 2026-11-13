import React from 'react'
import { Link } from 'react-router-dom'
import { StatusIndicator } from '../components/StatusIndicator'
import { Mic, BookOpen, Layers } from 'lucide-react'

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Mic className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
                  VoxLedger<span className="text-emerald-600">.ai</span>
                </span>
                <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">
                  PHASE 1
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium hidden sm:block">
                Multilingual AI Voice Accounting for Kirana & Retail
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <Link to="/" className="hover:text-emerald-600 transition-colors flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-emerald-600" />
              Architecture
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-emerald-600 transition-colors flex items-center gap-1.5"
            >
              <BookOpen className="w-4 h-4 text-slate-400" />
              API Docs
            </a>
          </nav>

          {/* Right Section: Live Health Pill */}
          <div className="flex items-center gap-3">
            <StatusIndicator />
          </div>
        </div>
      </div>
    </header>
  )
}
