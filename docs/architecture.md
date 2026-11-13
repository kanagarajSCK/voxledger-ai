# VoxLedger AI — System Architecture Document
## Phase 2: Core Ledger Engine & Functional Dashboard

### 1. High-Level Architecture Overview

VoxLedger AI is built as a high-performance, modular full-stack application designed to empower small retail merchants and kirana shopkeepers across India with natural voice-driven bookkeeping.

```
┌────────────────────────────────────────────────────────┐
│                   CLIENT TIER                           │
│   React 18 + TypeScript + Vite + Tailwind CSS          │
│   • Desktop & Android Mobile Browser Optimized         │
│   • TanStack Query for Async Server State Management    │
│   • Lucide React Icons & Kirana UI Design Tokens       │
│   • Two-Step Transaction Modals & Real-Time Validation │
│   • Customer Ledger Timeline & Balance Dashboard       │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / REST & WebSockets
                           ▼
┌────────────────────────────────────────────────────────┐
│                   BACKEND TIER                          │
│   FastAPI 0.115+ (Python 3.11+)                        │
│   • Async Lifespan & Dependency Injection System       │
│   • Pydantic v2 Settings & Validation                  │
│   • Structured Error Interceptors (400, 404, 409, 422) │
│   • Ledger Engine Service (Atomic Decimal Math)        │
│   • CORS Security Controls                             │
├──────────────────────────┬─────────────────────────────┤
│  REST API Gateway        │  Realtime Voice WS Gateway  │
│  /api/v1/customers       │  /api/v1/ws/voice           │
│  /api/v1/transactions    │  (Ready for Gnani Voice     │
│  /api/v1/dashboard       │   Bidirectional Streaming)  │
└──────────────────────────┴─────────────────────────────┘
                           │ Async SQLAlchemy 2.0 Engine
                           ▼
┌────────────────────────────────────────────────────────┐
│                   PERSISTENCE TIER                     │
│   SQLite Database (via aiosqlite Async Driver)         │
│   • Alembic Migration Control (batch alter table)      │
│   • PRAGMA foreign_keys = ON                           │
│   • Customer Model (UUID public IDs, Optional Phone)   │
│   • Transaction Model (Numeric(12,2) Exact Decimals,   │
│     CREDIT / PAYMENT Enum, Idempotency Protection,     │
│     Audit Reversals, ondelete=RESTRICT)                │
└────────────────────────────────────────────────────────┘
```

### 2. Database Schema (Phase 2 Current)

#### `customers` Table
- `id`: Integer Primary Key (Autoincrement)
- `public_id`: String(36) UUID v4, Indexed, Unique
- `name`: String(100), Indexed, Not Null
- `phone`: String(20), Indexed, Nullable
- `address`: String(255), Nullable
- `created_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- `updated_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- Relationship: `transactions` with cascade="all", passive_deletes="all"

#### `transactions` Table
- `id`: Integer Primary Key (Autoincrement)
- `public_id`: String(36) UUID v4, Indexed, Unique
- `customer_id`: Integer, Foreign Key `customers.id`, Indexed, `ondelete="RESTRICT"`
- `amount`: Numeric(12, 2), Not Null (Exact decimal representation for financial ledger calculations)
- `type`: Enum (`CREDIT`: Udhar Diya, `PAYMENT`: Paisa Mila / Settled Debt)
- `status`: Enum (`COMPLETED`, `REVERSED`), Default `COMPLETED`
- `idempotency_key`: String(64), Unique, Indexed, Nullable (Deduplication mechanism)
- `reversal_reason`: String(255), Nullable
- `description`: String(255), Nullable
- `voice_raw_text`: Text, Nullable (Audit record of raw transcribed phrase)
- `created_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`, Indexed
- `updated_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- Relationship: `customer`

---

### 3. Core Ledger Engine Rules & Invariants

1. **Balance Formula**:
   $$\text{Outstanding Balance} = \sum_{t \in \text{COMPLETED CREDIT}} t.\text{amount} - \sum_{t \in \text{COMPLETED PAYMENT}} t.\text{amount}$$
2. **Fixed-Point Arithmetic**:
   All monetary amounts are validated and calculated with Python `Decimal` and database column `Numeric(12, 2)`. No floating-point math is ever used.
3. **Transaction Validation**:
   - `amount > 0.00`: Zero and negative amounts rejected with HTTP 422.
   - `PAYMENT <= outstanding_balance`: A customer cannot pay more than their outstanding balance; overpayments are rejected with HTTP 400 (`PAYMENT_EXCEEDS_BALANCE`).
   - Customer existence is strictly checked before writing transactions.
4. **Idempotency Guard**:
   Submissions with the same `idempotency_key` return the original transaction without creating duplicate debt or payments.
5. **Customer Deletion Integrity**:
   Deleting a customer with transactions is blocked by database foreign key constraint (`ondelete="RESTRICT"`) and pre-validated at the service layer, returning HTTP 409 (`CUSTOMER_HAS_TRANSACTIONS`).

---

### 4. Realtime Voice Streaming Protocol (WebSocket Scaffold)

Endpoint: `/api/v1/ws/voice`

Handshake Sequence:
1. Client connects via WebSocket (`ws://` or `wss://`).
2. Server accepts and issues `connection_ack` with `client_id` and timestamp.
3. Client exchanges `ping`/`pong` heartbeats to track network latency.
4. Client sends `stream_init` with audio properties (e.g. `language: "hi-IN"`, `sample_rate: 16000`).
5. Server acknowledges with `stream_ready` and `session_id`, ready for audio frame streaming in Phase 3.
