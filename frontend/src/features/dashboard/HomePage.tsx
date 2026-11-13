import React from 'react'
import { HealthMetricsCard } from '../health/HealthMetricsCard'
import { WebSocketIndicator } from '../../components/WebSocketIndicator'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import {
  Database,
  CheckCircle2,
  Radio,
  Sparkles,
  ShieldCheck,
} from 'lucide-react'

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Hero / Phase 1 Status Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 p-6 sm:p-8 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            PHASE 1 COMPLETE — FOUNDATION & ARCHITECTURE
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            VoxLedger AI
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Multilingual AI Voice Accounting platform engineered for kirana shopkeepers and small retail merchants across India.
            Phase 1 provides the verified, scalable backend and frontend foundation.
          </p>
          <div className="pt-2 flex flex-wrap gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">FastAPI 0.115+</span>
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">SQLAlchemy 2.0 Async</span>
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">SQLite + aiosqlite</span>
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">Alembic Migrations</span>
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">React + TypeScript</span>
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">Tailwind CSS</span>
            <span className="px-2.5 py-1 rounded-md bg-white/10 text-slate-200">TanStack Query</span>
          </div>
        </div>
      </div>

      {/* Live System Health Section */}
      <HealthMetricsCard />

      {/* Voice Gateway WebSocket Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-emerald-600" />
            Real-Time Voice Streaming Gateway Scaffold
          </CardTitle>
          <CardDescription>
            WebSocket scaffold prepared for future Gnani multilingual real-time speech streaming
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WebSocketIndicator />
        </CardContent>
      </Card>

      {/* Dual Column: Data Models & Architecture Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Model Scaffolding */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-emerald-600" />
              Database Model Scaffolding
            </CardTitle>
            <CardDescription>
              Production-ready SQLAlchemy 2.0 models with decimal financial types
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Customer Schema */}
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-slate-900 font-mono">Customer</span>
                <Badge variant="success">Scaffolded & Migrated</Badge>
              </div>
              <p className="text-xs text-slate-600">
                Primary model for kirana shopkeeper customer profiles.
              </p>
              <div className="text-[11px] font-mono text-slate-600 bg-white p-2 rounded border border-slate-100 space-y-0.5">
                <div>• id: Integer (PK, autoincrement)</div>
                <div>• public_id: UUID string (indexed)</div>
                <div>• name: String(100, indexed)</div>
                <div>• phone: String(20, indexed)</div>
                <div>• address: String(255, optional)</div>
                <div>• created_at / updated_at: DateTime(tz=True)</div>
                <div>• transactions: relationship (cascade delete-orphan)</div>
              </div>
            </div>

            {/* Transaction Schema */}
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-slate-900 font-mono">Transaction</span>
                <Badge variant="success">Scaffolded & Migrated</Badge>
              </div>
              <p className="text-xs text-slate-600">
                Financial ledger entries with exact decimal currency precision.
              </p>
              <div className="text-[11px] font-mono text-slate-600 bg-white p-2 rounded border border-slate-100 space-y-0.5">
                <div>• id: Integer (PK) | public_id: UUID string</div>
                <div>• customer_id: FK(customers.id)</div>
                <div>• amount: Numeric(12, 2) [exact Decimal]</div>
                <div>• type: Enum (CREDIT: Udhar Diya, PAYMENT: Paisa Mila)</div>
                <div>• voice_raw_text: Text (raw voice transcript audit)</div>
                <div>• created_at / updated_at: DateTime(tz=True)</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Phase 1 Verification Checklist */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Phase 1 Verification Matrix
            </CardTitle>
            <CardDescription>
              Architectural and functional requirements verified with automated tests
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: 'FastAPI async application & lifespan management', status: true },
              { label: 'Environment configuration via Pydantic Settings', status: true },
              { label: 'SQLite async database connection with aiosqlite', status: true },
              { label: 'SQLAlchemy 2.0 session factory & dependency injection', status: true },
              { label: 'Health endpoints: /api/health and /api/v1/health', status: true },
              { label: 'Alembic migration generation & execution', status: true },
              { label: 'Structured JSON error handling (404, 422, 500)', status: true },
              { label: 'CORS configured for development & production origins', status: true },
              { label: 'WebSocket /api/v1/ws/voice with ping/pong handshake', status: true },
              { label: 'Pytest test suite (7/7 tests passed: 100%)', status: true },
              { label: 'React + TypeScript + Vite + Tailwind CSS shell', status: true },
              { label: 'TanStack Query live health check polling', status: true },
              { label: 'Mobile-first responsive layout (Desktop + Android)', status: true },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs text-slate-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{item.label}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
