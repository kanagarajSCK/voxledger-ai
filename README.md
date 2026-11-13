# VoxLedger AI — Multilingual Voice Accounting Platform

VoxLedger AI is a hackathon-grade, multilingual AI voice accounting platform built for small retail businesses and kirana shopkeepers across India. It empowers shopkeepers to effortlessly track credit (*udhar*), payments (*jama*), outstanding customer balances, and transaction history using natural, conversational voice interactions in Indic languages.

---

## 1. Technology Stack

### Backend
- **Framework**: Python 3.11+ / FastAPI 0.115+
- **ASGI Server**: Uvicorn (standard)
- **Data Validation & Settings**: Pydantic v2 & Pydantic-Settings
- **ORM**: SQLAlchemy 2.0 (Async)
- **Database Engine**: SQLite with `aiosqlite` async driver
- **Migrations**: Alembic
- **Real-Time Streaming**: Native WebSockets (`/api/v1/ws/voice`)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX, Starlette TestClient

### Frontend
- **Core**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with custom kirana-friendly palette and touch-friendly mobile targets
- **Icons**: Lucide React
- **Routing**: React Router DOM (v6/v7)
- **Server State**: TanStack Query (React Query v5)
- **Testing**: Vitest, React Testing Library, JSDOM

---

## 2. Prerequisites

- **Operating System**: Windows 11 / macOS / Linux
- **Python**: 3.11 or newer (Python 3.14 compatible)
- **Node.js**: v18.0.0 or newer (v25 tested)
- **Package Managers**: `pip` (Python) and `npm` (Node)

---

## 3. Project Structure

```text
voxledger-ai/
├── frontend/                     # React + TypeScript Vite frontend
│   ├── public/                   # Static public assets
│   ├── src/
│   │   ├── app/                  # App component, routing, providers
│   │   ├── components/           # Reusable UI primitives (Buttons, Cards, Badges)
│   │   ├── features/             # Feature modules (Dashboard, Health, Not Found)
│   │   ├── hooks/                # Custom React hooks (useHealthCheck, useVoiceWebSocket)
│   │   ├── layouts/              # Reusable layouts (RootLayout, Header, MobileNav)
│   │   ├── lib/                  # Utilities and typed API client
│   │   ├── services/             # Backend service integrations
│   │   ├── styles/               # Global CSS & Tailwind configuration
│   │   ├── types/                # TypeScript interfaces and API schemas
│   │   ├── tests/                # Vitest & React Testing Library suites
│   │   └── main.tsx              # DOM mount entrypoint
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                      # FastAPI async backend
│   ├── alembic/                  # Database migration scripts
│   ├── app/
│   │   ├── api/                  # Versioned API routes (/api/v1)
│   │   ├── core/                 # Settings, configuration, error handling
│   │   ├── db/                   # Async session & SQLAlchemy base declarative
│   │   ├── models/               # Scaffolding models (Customer, Transaction)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── services/             # Business logic layer
│   │   ├── websocket/            # WebSocket connection manager & voice endpoint
│   │   └── main.py               # FastAPI application entrypoint & lifespan
│   ├── tests/                    # Pytest test suite
│   ├── alembic.ini               # Alembic configuration
│   └── requirements.txt          # Python dependencies
├── docs/                         # Architectural diagrams and documentation
├── .env.example                  # Environment configuration template
├── .gitignore                    # Secrets, virtualenvs, and build artifacts
├── README.md                     # Project documentation & startup guide
└── PROJECT_STATUS.md             # Phase tracking & instructions for next agent
```

---

## 4. Installation Instructions

### Clone / Open Project
```powershell
cd D:\Projects\voxledger-ai
```

### Backend Setup
1. Create and activate a Python virtual environment:
   ```powershell
   python -m venv backend/venv
   .\backend\venv\Scripts\Activate.ps1
   ```
2. Install Python dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. Run database migrations:
   ```powershell
   cd backend
   .\venv\Scripts\alembic.exe upgrade head
   cd ..
   ```

### Frontend Setup
1. Install npm dependencies:
   ```powershell
   npm install --prefix frontend
   ```

### Environment Configuration
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

---

## 5. Startup Commands

### Start Backend Development Server
From the root directory:
```powershell
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **WebSocket Voice Endpoint**: `ws://localhost:8000/api/v1/ws/voice`

### Start Frontend Development Server
In a separate terminal:
```powershell
npm run dev --prefix frontend
```
- **Frontend URL**: [http://localhost:5173](http://localhost:5173)

---

## 6. Running Automated Tests

### Run Backend Tests (Pytest)
```powershell
.\backend\venv\Scripts\python.exe -m pytest backend -v
```
All 7 unit and integration tests run against an isolated SQLite test database.

### Run Frontend Tests (Vitest)
```powershell
npm run test --prefix frontend
```
Runs component and application shell integration tests via Vitest and JSDOM.

### Frontend Production Build Verification
```powershell
npm run build --prefix frontend
```
Verifies strict TypeScript type-checking and compiles optimized static assets.
