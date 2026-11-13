# VoxLedger AI — Project Status & Handoff Guide

## 1. Current Phase
**PHASE 1: Advanced Project Foundation & Architecture** — **COMPLETED AND FULLY VERIFIED**

---

## 2. Architecture Decisions
1. **Monorepo Layout**:
   - Clean separation of concerns between `backend/` (FastAPI) and `frontend/` (React + Vite).
   - Root-level configuration (`.env`, `.env.example`, `.gitignore`, `README.md`, `PROJECT_STATUS.md`, `docs/`).
2. **Database Engine & ORM**:
   - SQLite with `aiosqlite` async driver for zero-configuration, cross-platform portability.
   - SQLAlchemy 2.0 modern declarative syntax (`Mapped`, `mapped_column`, `relationship`).
   - `PRAGMA foreign_keys = ON` enforced via event listeners on engine connection to guarantee cascade integrity.
   - Exact financial precision: `Numeric(12, 2)` (represented as Python `Decimal`) to eliminate IEEE 754 floating-point errors in ledger calculations.
   - Alembic migrations configured for async SQLAlchemy engine.
3. **API & Communication**:
   - Versioned API prefix `/api/v1` with an unversioned alias `/api/health` for generic cloud health probes.
   - Standardized structured error response format with UTC ISO-8601 timestamps and distinct error codes.
   - Dedicated WebSocket endpoint `/api/v1/ws/voice` with `ConnectionManager` scaffolded for future bidirectional streaming (Gnani AI speech-to-text / text-to-speech).
4. **Frontend Architecture**:
   - React 18 + TypeScript + Vite + Tailwind CSS.
   - TanStack Query v5 for server state polling and caching.
   - Dual-viewport layout design: Responsive desktop navigation + Android mobile bottom navigation bar with 48px touch targets for kirana merchants.
   - Live backend health polling indicator with millisecond database latency metrics.

---

## 3. Files Created and Modified

### Root
- `.env.example` — Environment configuration template.
- `.env` — Local development environment settings.
- `.gitignore` — Version control ignore rules (venv, node_modules, build artifacts, databases).
- `README.md` — Project documentation and setup guide.
- `PROJECT_STATUS.md` — Current phase status, test verification records, and handoff instructions.

### Documentation
- `docs/architecture.md` — System architecture and WebSocket handshake documentation.

### Backend (`backend/`)
- `requirements.txt` — Python dependencies with version pins.
- `pytest.ini` — Pytest configuration with `asyncio_mode = auto` and warning suppressions.
- `alembic.ini` — Alembic migration runner configuration.
- `verify_live.py` — Live end-to-end verification script testing REST and WebSockets against live Uvicorn.
- `app/main.py` — FastAPI application initialization, lifespan management, CORS middleware, error registration.
- `app/core/config.py` — Pydantic Settings class with environment variable parsing.
- `app/core/errors.py` — Structured error models and global exception handlers (404, 422, 500, AppException).
- `app/db/base.py` — SQLAlchemy declarative base with standard constraint naming conventions.
- `app/db/session.py` — Async engine, session factory, `get_db` dependency, SQLite foreign key enabler.
- `app/models/customer.py` — `Customer` SQLAlchemy 2.0 model with UUID public ID and cascade relationships.
- `app/models/transaction.py` — `Transaction` model with `Numeric(12, 2)` decimal amounts and `TransactionType` enum.
- `app/models/__init__.py` — Package export for declarative models.
- `app/schemas/health.py` — Pydantic validation schema for `/health` response.
- `app/schemas/customer.py` — Pydantic schemas for customer creation and response.
- `app/schemas/transaction.py` — Pydantic schemas for transaction creation and response.
- `app/schemas/__init__.py` — Package schema exports.
- `app/websocket/connection_manager.py` — WebSocket connection manager for client lifecycle management.
- `app/websocket/voice_ws.py` — WebSocket endpoint `/api/v1/ws/voice` with ping/pong and `stream_init` envelope.
- `app/websocket/__init__.py` — WebSocket router exports.
- `app/api/v1/router.py` — Version 1 API router registering health and WebSocket endpoints.
- `app/api/v1/endpoints/health.py` — Async health check endpoint querying `SELECT 1` with latency measurement.
- `alembic/env.py` — Async Alembic environment migration runner.
- `alembic/script.py.mako` — Alembic migration template.
- `alembic/versions/2c1138bdc9d7_initial_schema_for_customers_and_.py` — Initial migration for customers and transactions.
- `tests/conftest.py` — Isolated async test database fixtures, `async_client`, and `sync_client`.
- `tests/test_health.py` — Tests for `/api/health`, `/api/v1/health`, and `/`.
- `tests/test_models.py` — Tests for Customer and Transaction creation, relationships, and cascade deletes.
- `tests/test_websocket.py` — Tests for WebSocket connection handshake, ping/pong, and `stream_init`.
- `tests/test_errors.py` — Tests for 404 structured error responses.

### Frontend (`frontend/`)
- `package.json` — Frontend dependencies and scripts (`dev`, `build`, `test`).
- `tsconfig.json` & `src/vite-env.d.ts` — TypeScript compiler configuration with path aliases and Vite client types.
- `vite.config.ts` — Vite bundler configuration with proxy rules and Vitest integration.
- `tailwind.config.js` — Tailwind CSS configuration with custom emerald brand and credit/debit colors.
- `postcss.config.js` — PostCSS configuration.
- `index.html` — HTML shell with responsive mobile viewport meta tags.
- `src/main.tsx` — Application DOM mount entrypoint.
- `src/app/App.tsx` — Top-level App component wrapping routes in providers.
- `src/app/router.tsx` — React Router browser router configuration.
- `src/app/providers.tsx` — TanStack QueryClientProvider wrapper.
- `src/styles/index.css` — Global CSS with Tailwind directives and kirana touch targets.
- `src/lib/api.ts` — Typed `apiClient` with base URL fallback and error translation.
- `src/lib/utils.ts` — Utility class merging (`clsx` + `twMerge`).
- `src/services/healthService.ts` — Health API fetch functions.
- `src/types/api.ts` & `src/types/health.ts` — TypeScript type definitions.
- `src/hooks/useHealthCheck.ts` — TanStack Query polling hook for system health.
- `src/hooks/useVoiceWebSocket.ts` — WebSocket client hook for voice streaming gateway.
- `src/components/ui/Badge.tsx` — Status badge component.
- `src/components/ui/Button.tsx` — Reusable button with variants and loading spinner.
- `src/components/ui/Card.tsx` — Accessible card component.
- `src/components/ui/LoadingSpinner.tsx` — Animated loading spinner.
- `src/components/ui/ErrorAlert.tsx` — Error alert component with retry trigger.
- `src/components/StatusIndicator.tsx` — Live health pill with ping latency badge.
- `src/components/WebSocketIndicator.tsx` — Interactive WebSocket tester with ping/pong latency.
- `src/layouts/RootLayout.tsx` — Responsive layout shell.
- `src/layouts/Header.tsx` — Application header with status indicator.
- `src/layouts/MobileNav.tsx` — Bottom navigation bar for mobile touch screens.
- `src/features/dashboard/HomePage.tsx` — Phase 1 Foundation dashboard with verification checklist.
- `src/features/health/HealthMetricsCard.tsx` — Backend health metrics display card.
- `src/features/not-found/NotFoundPage.tsx` — 404 fallback page.
- `src/tests/setup.ts` — Vitest test setup with `jest-dom`.
- `src/tests/App.test.tsx` — App shell and brand rendering tests.
- `src/tests/HealthMetricsCard.test.tsx` — Health metrics component render test.

---

## 4. Features Completed
- [x] Monorepo directory structure established.
- [x] FastAPI async application with lifespan management and structured logging.
- [x] SQLite + `aiosqlite` async connection pool with `PRAGMA foreign_keys = ON`.
- [x] Scaffolding database models: `Customer` and `Transaction` with `Numeric(12, 2)` monetary values.
- [x] Alembic migration `2c1138bdc9d7` generated and applied (`alembic upgrade head`).
- [x] Health check endpoints: `GET /api/health` and `GET /api/v1/health` with DB roundtrip latency.
- [x] Structured JSON error handling across all HTTP and validation exceptions.
- [x] CORS middleware configured for development and production origins.
- [x] WebSocket voice streaming gateway scaffold at `/api/v1/ws/voice` with connection manager.
- [x] Pytest automated test suite (7/7 tests passed: 100%).
- [x] React + TypeScript + Vite + Tailwind CSS frontend shell.
- [x] TanStack Query health check polling with live status indicator pill.
- [x] Vitest + React Testing Library automated test suite (2 test files, 3/3 tests passed: 100%).
- [x] Frontend TypeScript strict compilation (`tsc -b && vite build`) passed with zero errors.
- [x] Live end-to-end communication verified between frontend and backend.
- [x] Environment configuration files (`.env`, `.env.example`) and `.gitignore` committed.

---

## 5. Commands Executed & Verification Results

### Backend Unit & Integration Tests (Pytest)
```powershell
.\backend\venv\Scripts\python.exe -m pytest backend -v
```
**Result**:
```text
backend\tests\test_errors.py::test_404_structured_error PASSED           [ 14%]
backend\tests\test_health.py::test_unversioned_health_check PASSED       [ 28%]
backend\tests\test_health.py::test_versioned_health_check PASSED         [ 42%]
backend\tests\test_health.py::test_root_endpoint PASSED                  [ 57%]
backend\tests\test_models.py::test_create_customer_and_transactions PASSED [ 71%]
backend\tests\test_models.py::test_customer_cascade_delete PASSED        [ 85%]
backend\tests\test_websocket.py::test_websocket_connection_and_handshake PASSED [100%]
======================== 7 passed, 2 warnings in 1.86s ========================
```

### Alembic Migration Verification
```powershell
cd backend; .\venv\Scripts\alembic.exe upgrade head; cd ..
```
**Result**:
```text
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 2c1138bdc9d7, Initial schema for customers and transactions
```

### Frontend Unit & Component Tests (Vitest)
```powershell
npm run test --prefix frontend
```
**Result**:
```text
 ✓ src/tests/HealthMetricsCard.test.tsx (1 test) 220ms
 ✓ src/tests/App.test.tsx (2 tests) 709ms
 Test Files  2 passed (2)
      Tests  3 passed (3)
```

### Frontend Production Build (TypeScript + Vite)
```powershell
npm run build --prefix frontend
```
**Result**:
```text
vite v5.4.21 building for production...
✓ 1651 modules transformed.
dist/index.html                   0.59 kB │ gzip:  0.39 kB
dist/assets/index-CsLf2fdM.css   20.83 kB │ gzip:  4.75 kB
dist/assets/index-DQutB1wq.js   295.33 kB │ gzip: 93.28 kB
✓ built in 19.33s
```

### Live Server Integration Test (`backend/verify_live.py`)
```powershell
cd backend; .\venv\Scripts\python.exe verify_live.py; cd ..
```
**Result**:
```text
REST /api/health -> VERIFIED (200 OK, DB Connected)
REST /api/v1/health -> VERIFIED (200 OK)
REST / -> VERIFIED (200 OK)
REST 404 Structured Error -> VERIFIED
WS ACK RECEIVED: {"type":"connection_ack", ...}
WS PONG RECEIVED: {"type":"pong", ...}
WS STREAM_READY RECEIVED: {"type":"stream_ready", ...}
WEBSOCKET /api/v1/ws/voice -> VERIFIED (Handshake + Ping + StreamInit)
ALL PHASE 1 BACKEND VERIFICATIONS COMPLETED SUCCESSFULLY!
```

---

## 6. Known Errors & Issues
- **None**. All tests are passing, migrations are current, and production build succeeds with zero errors.

---

## 7. Pending Tasks for Phase 2
- Phase 2: Core Ledger & Customer Management:
  - Customer CRUD endpoints and business logic.
  - Transaction record creation with credit/payment balance calculations.
  - Customer summary balances (total credit given, total payments received, net outstanding).
  - Premium kirana shopkeeper UI: Customer directory, Ledger timeline, Transaction modal, Search & filtering.
  - Multilingual voice transaction input preparation.

---

## 8. Instructions for Next AI Coding Agent (or VS Code + GitHub Copilot)

If you are continuing this project in VS Code with GitHub Copilot:
1. **Virtual Environment**:
   - Activate the existing virtual environment:
     ```powershell
     .\backend\venv\Scripts\Activate.ps1
     ```
2. **Starting Servers**:
   - Backend:
     ```powershell
     .\backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
     ```
   - Frontend:
     ```powershell
     npm run dev --prefix frontend
     ```
3. **Database Migrations**:
   - Whenever models in `backend/app/models/` are added or changed:
     ```powershell
     cd backend
     .\venv\Scripts\alembic.exe revision --autogenerate -m "Your migration description"
     .\venv\Scripts\alembic.exe upgrade head
     cd ..
     ```
4. **Verifying Code**:
   - Always run both test suites before claiming a task is done:
     ```powershell
     .\backend\venv\Scripts\python.exe -m pytest backend -v
     npm run test --prefix frontend
     npm run build --prefix frontend
     ```
5. **Phase Control**:
   - Do NOT begin Phase 2 until the user reviews Phase 1 and gives explicit approval.
