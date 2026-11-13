# VoxLedger AI — Multilingual Voice Accounting Platform

VoxLedger AI is a hackathon-grade, multilingual AI voice accounting platform built for small retail businesses and kirana shopkeepers across India. It empowers shopkeepers to effortlessly track credit (*udhar*), payments (*jama*), outstanding customer balances, and transaction history using natural, conversational voice interactions in Indic languages.

---

## 1. Technology Stack

### Backend
- **Framework**: Python 3.11+ / FastAPI 0.115+
- **Voice AI Engines**:
  - **STT**: Gnani Prisma v3.0 (`wss://api.vachana.ai/stt/v3/stream`) via live bidirectional 16kHz linear PCM streaming
  - **TTS**: Gnani Timbre v3.0 (`https://api.vachana.ai/api/v1/tts/inference`) with verified Indic voices (`Shivani` for Hindi, English, Tamil, Kannada)
- **ASGI Server**: Uvicorn (standard)
- **Data Validation & Settings**: Pydantic v2 & Pydantic-Settings (Credentials secured via `SecretStr`)
- **Financial Precision**: Python `Decimal` and SQLAlchemy `Numeric(12, 2)` (zero floating-point arithmetic)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Database Engine**: SQLite with `aiosqlite` async driver
- **Migrations**: Alembic (`render_as_batch=True` for SQLite schema alterations)
- **Real-Time Streaming**: Native WebSockets (`/api/v1/ws/voice`)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX, Starlette TestClient (33 tests)

### Frontend
- **Core**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with custom kirana-friendly palette (emerald, midnight navy, warm ivory) and touch-friendly mobile targets (min 44px)
- **Icons**: Lucide React
- **Audio Capture**: Web Audio API downsampling hardware mic streams to 16,000 Hz 16-bit mono signed linear PCM
- **Routing**: React Router DOM
- **Server State**: TanStack Query (React Query v5) with query invalidation
- **Testing**: Vitest, React Testing Library, JSDOM (15 tests)

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

## 3. Real-Time Voice Pipeline & Safety Barrier

VoxLedger AI features a zero-loss financial safety state machine for voice interactions:

- **No Direct Database Writes from Voice**: Transcribed speech from Gnani Prisma v3.0 is parsed by the Indic `IntentParser`, cross-checked with the customer database, and evaluated against balance constraints.
- **Two-Step Confirmation Required**:
  1. The assistant displays a prominent **Verification Card** detailing the Customer Name, Transaction Type, Amount, Current Balance, and Projected Balance.
  2. The assistant synthesizes a confirmation prompt via Gnani Timbre v3.0 (e.g. *"Ramesh-ku 340 rupees udhaar podalama?"*).
  3. The action is committed **only** upon explicit shopkeeper confirmation (*"Yes"*, *"Sari"*, *"Haan"*, or clicking the Confirm button).
- **Natural Voice Corrections**: If the shopkeeper makes a mistake, they can correct it conversationally (*"Ramesh-ku 500 illa, 350"* or *"500 nahi, 350 rupees"*). The system updates the pending proposal in real time without executing the invalid state.
- **Natural Voice Cancellations**: Saying *"No"*, *"Nahi"*, *"Vendaam"*, or clicking Cancel safely discards the pending proposal.

### Supported Voice Dialects & Examples

| Language / Dialect | Example Credit Phrase | Example Payment Phrase | Example Balance Query |
|---|---|---|---|
| **Hinglish / Hindi** | *"Ramesh ka 340 rupaye udhar likho"* | *"Ramesh ne 200 jama kiya"* | *"Ramesh ka balance kitna hai?"* |
| **Tanglish / Tamil** | *"Ramesh-ku 340 rupees udhaar podu"* | *"Ramesh 200 rupees paid"* | *"Ramesh-ku evvalavu balance irukku?"* |
| **English (`en-IN`)** | *"Give credit of 340 rupees to Ramesh"* | *"Ramesh paid 200 rupees"* | *"How much does Ramesh owe?"* |
| **Kannada (`kn-IN`)** | *"Ramesh-ge 340 rupees saala kodi"* | *"Ramesh 200 rupees kottiddare"* | *"Ramesh baaki eshtu ide?"* |

---

## 4. API Endpoints Reference

### Voice Endpoints (`/api/v1/voice`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/voice/status` | Returns Gnani STT and TTS configuration status, models, and default voice |
| `POST` | `/api/v1/voice/tts` | Synthesize speech using Gnani Timbre v3.0 (returns base64 WAV) |
| `GET` | `/api/v1/voice/tts` | Query-param based audio stream endpoint for web players |
| `WS` | `/api/v1/ws/voice` | Full-duplex WebSocket for raw 16kHz PCM audio streaming & control frames |

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

### System & Health
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Root health-check endpoint |
| `GET` | `/api/v1/health` | Versioned v1 health-check endpoint |

---

## 5. Quickstart & Testing

### Running Tests
- **Backend (Pytest)**:
  ```powershell
  .\backend\venv\Scripts\python.exe -m pytest backend -v
  ```
- **Frontend (Vitest)**:
  ```powershell
  npm test --prefix frontend
  ```
- **Live Gnani Verification**:
  ```powershell
  .\backend\venv\Scripts\python.exe backend/verify_gnani_live.py
  ```

### Running the Full-Stack Application
1. **Start Backend**:
   ```powershell
   cd backend
   .\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```
2. **Start Frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser. Click the **Voice Khata** button or press the central microphone on mobile to start speaking in Hindi, Tamil, English, or Kannada!
