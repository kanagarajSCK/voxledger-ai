import React from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { MobileNav } from './MobileNav'

export const RootLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 pb-16 md:pb-0">
      <Header />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white py-6 hidden md:block">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 VoxLedger AI. Multilingual Kirana & Retail Voice Accounting Platform.</p>
          <div className="flex items-center gap-4">
            <span>FastAPI + SQLite + SQLAlchemy 2.0</span>
            <span>•</span>
            <span>React + Vite + Tailwind CSS</span>
          </div>
        </div>
      </footer>
      <MobileNav />
    </div>
  )
}
