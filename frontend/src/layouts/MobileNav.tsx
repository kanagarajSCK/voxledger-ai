import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Layers, Activity, BookOpen } from 'lucide-react'
import { cn } from '../lib/utils'

export const MobileNav: React.FC = () => {
  const location = useLocation()

  const navItems = [
    { label: 'Foundation', path: '/', icon: Layers },
    { label: 'API Docs', path: 'http://localhost:8000/docs', external: true, icon: BookOpen },
    { label: 'Health', path: '#health-section', external: false, icon: Activity },
  ]

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-slate-200 px-4 py-2 flex items-center justify-around shadow-lg pb-[max(0.5rem,env(safe-area-inset-bottom))]">
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = location.pathname === item.path

        if (item.external) {
          return (
            <a
              key={item.label}
              href={item.path}
              target="_blank"
              rel="noreferrer"
              className="flex flex-col items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-emerald-600 touch-target justify-center"
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </a>
          )
        }

        return (
          <Link
            key={item.label}
            to={item.path}
            className={cn(
              'flex flex-col items-center gap-1 text-[11px] font-medium touch-target justify-center transition-colors',
              isActive ? 'text-emerald-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
            )}
          >
            <Icon className="w-5 h-5" />
            <span>{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
