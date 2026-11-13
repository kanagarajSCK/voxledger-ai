# VoxLedger AI — Multilingual Voice Accounting Platform

VoxLedger AI is a hackathon-grade, multilingual AI voice accounting platform built for small retail businesses and kirana shopkeepers across India. It empowers shopkeepers to effortlessly track credit (*udhar*), payments (*jama*), outstanding customer balances, and transaction history using natural, conversational voice interactions in Indic languages.

---

## 1. Technology Stack

### Backend
- **Framework**: Python 3.11+ / FastAPI 0.115+
- **ASGI Server**: Uvicorn (standard)
- **Data Validation & Settings**: Pydantic v2 & Pydantic-Settings
- **Financial Precision**: Python `Decimal` and SQLAlchemy `Numeric(12, 2)` (zero floating-point arithmetic)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Database Engine**: SQLite with `aiosqlite` async driver
- **Migrations**: Alembic (`render_as_batch=True` for SQLite schema alterations)
- **Real-Time Streaming**: Native WebSockets (`/api/v1/ws/voice`)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX, Starlette TestClient (18 tests)

### Frontend
- **Core**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with custom kirana-friendly palette (emerald, midnight navy, warm ivory) and touch-friendly mobile targets (min 44px)
- **Icons**: Lucide React
- **Routing**: React Router DOM
- **Server State**: TanStack Query (React Query v5) with query invalidation
- **Testing**: Vitest, React Testing Library, JSDOM (10 tests)

---

## 2. Core Ledger Architecture & Financial Rules

VoxLedger AI enforces strict financial accounting rules:

1. **Balance Formula**:
   $$\text{Outstanding Balance} = \sum \text{CREDIT} - \sum \text{PAYMENT}$$
2. **Fixed-Point Decimal Arithmetic**:
   All monetary amounts are validated and stored using Python `Decimal` and database column `Numeric(12, 2)`. Floating-point math is strictly forbidden.
3. **Transaction Validation**:
   - `amount > 0.00`: Zero or negative transactions are rejected with HTTP 422.
   - `PAYMENT <= outstanding_balance`: A payment cannot exceed what the customer currently owes; overpayments are rejected with structured HTTP 400 (`PAYMENT_EXCEEDS_BALANCE`).
   - Customer existence is strictly verified before writing transactions.
4. **Idempotency & Duplicate Prevention**:
   Every transaction submission includes a unique `idempotency_key` (String 64). Re-submitting the same key atomically returns the original transaction record without duplicating money.
5. **Customer Deletion Protection**:
   Deleting a customer with existing transaction history is blocked by database foreign key constraint (`ondelete="RESTRICT"`) and verified at the service layer, returning HTTP 409 (`CUSTOMER_HAS_TRANSACTIONS`). Financial audit trails cannot be silently erased.

---

## 3. API Endpoints Reference

### Customer Management (`/api/v1/customers`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/customers?search=&skip=0&limit=50` | Search customers by name/phone with pagination |
| `POST` | `/api/v1/customers` | Register customer (`name` required, `phone`, `address` optional) |
| `GET` | `/api/v1/customers/{customer_id}` | Retrieve customer profile and live balance summary |
| `PATCH` | `/api/v1/customers/{customer_id}` | Update customer name, phone, or address |
| `DELETE` | `/api/v1/customers/{customer_id}` | Delete customer (blocked if transactions exist) |

### Transaction Engine (`/api/v1/transactions`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/transactions` | Record `CREDIT` or `PAYMENT` with idempotency key |
| `GET` | `/api/v1/transactions?skip=0&limit=50` | List transactions with customer metadata |
| `GET` | `/api/v1/transactions/{transaction_id}` | Retrieve single transaction record |
| `GET` | `/api/v1/customers/{customer_id}/transactions` | Customer ledger statement |

### Dashboard Summary (`/api/v1/dashboard/summary`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Real-time aggregate statistics: total customers, total outstanding credit, today's credit, today's payments, and recent transactions |

### System & Streaming
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Root health-check endpoint |
| `GET` | `/api/v1/health` | Versioned v1 health-check endpoint |
| `WS` | `/api/v1/ws/voice` | Real-time WebSocket connection for voice streaming |

---

## 4. Installation Instructions

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
```powershell
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **WebSocket Voice Endpoint**: `ws://localhost:8000/api/v1/ws/voice`

### Start Frontend Development Server
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
**Results**: 18 passed, 0 failed in 5.62s (100% PASSING).

### Run Frontend Tests (Vitest)
```powershell
npm test --prefix frontend
```
**Results**: 4 test files, 10 passed, 0 failed in 25.47s (100% PASSING).

### Frontend Production Build Verification
```powershell
npm run build --prefix frontend
```
Compiles with zero TypeScript warnings or errors (`tsc -b && vite build`).
