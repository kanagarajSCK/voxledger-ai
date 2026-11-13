import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { StatusIndicator } from '../components/StatusIndicator'
import { Mic, BookOpen, Layers, Users, LayoutDashboard } from 'lucide-react'
import { cn } from '../lib/utils'

export const Header: React.FC = () => {
  const location = useLocation()

  const navLinks = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Customers', path: '/customers', icon: Users },
    { label: 'Architecture', path: '/foundation', icon: Layers },
  ]

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
                  PHASE 2
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium hidden sm:block">
                Multilingual AI Voice Accounting for Kirana & Retail
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 sm:gap-2 text-sm font-medium">
            {navLinks.map((link) => {
              const Icon = link.icon
              const isActive =
                link.path === '/'
                  ? location.pathname === '/'
                  : location.pathname.startsWith(link.path)

              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={cn(
                    'px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors',
                    isActive
                      ? 'bg-emerald-50 text-emerald-700 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  )}
                >
                  <Icon className={cn('w-4 h-4', isActive ? 'text-emerald-600' : 'text-slate-400')} />
                  {link.label}
                </Link>
              )
            })}

            <div className="h-4 w-px bg-slate-200 mx-2" />

            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors flex items-center gap-1.5"
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
