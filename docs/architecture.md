# VoxLedger AI — System Architecture Document
## Phase 1: Foundation & Architecture

### 1. High-Level Architecture Overview

VoxLedger AI is built as a high-performance, modular full-stack application designed to empower small retail merchants and kirana shopkeepers across India with natural voice-driven bookkeeping.

```
┌────────────────────────────────────────────────────────┐
│                   CLIENT TIER                           │
│   React 18 + TypeScript + Vite + Tailwind CSS          │
│   • Desktop & Android Mobile Browser Optimized         │
│   • TanStack Query for Async Server State Management    │
│   • Lucide React Icons & Kirana UI Design Tokens       │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / REST & WebSockets
                           ▼
┌────────────────────────────────────────────────────────┐
│                   BACKEND TIER                          │
│   FastAPI 0.115+ (Python 3.11+)                        │
│   • Async Lifespan & Dependency Injection System       │
│   • Pydantic v2 Settings & Validation                  │
│   • Structured Error Interceptors (404, 422, 500)      │
│   • CORS Security Controls                             │
├──────────────────────────┬─────────────────────────────┤
│  REST API Gateway        │  Realtime Voice WS Gateway  │
│  /api/health             │  /api/v1/ws/voice           │
│  /api/v1/health          │  (Ready for Gnani Voice     │
│  /api/v1/openapi.json    │   Bidirectional Streaming)  │
└──────────────────────────┴─────────────────────────────┘
                           │ Async SQLAlchemy 2.0 Engine
                           ▼
┌────────────────────────────────────────────────────────┐
│                   PERSISTENCE TIER                     │
│   SQLite Database (via aiosqlite Async Driver)         │
│   • Alembic Migration Control                          │
│   • PRAGMA foreign_keys = ON                           │
│   • Customer Model (UUID public IDs, Phone Indexing)   │
│   • Transaction Model (Numeric(12,2) Exact Decimals,   │
│     CREDIT / PAYMENT Enum, Cascade Deletes)            │
└────────────────────────────────────────────────────────┘
```

### 2. Database Schema Scaffolding

#### `customers` Table
- `id`: Integer Primary Key (Autoincrement)
- `public_id`: String(36) UUID v4, Indexed, Unique
- `name`: String(100), Indexed, Not Null
- `phone`: String(20), Indexed, Not Null
- `address`: String(255), Nullable
- `created_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- `updated_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- Relationship: `transactions` with cascade="all, delete-orphan"

#### `transactions` Table
- `id`: Integer Primary Key (Autoincrement)
- `public_id`: String(36) UUID v4, Indexed, Unique
- `customer_id`: Integer, Foreign Key `customers.id`, Indexed, OnDelete CASCADE
- `amount`: Numeric(12, 2), Not Null (Exact decimal representation for financial ledger calculations)
- `type`: Enum (`CREDIT`: Udhar Diya, `PAYMENT`: Paisa Mila / Settled Debt)
- `description`: String(255), Nullable
- `voice_raw_text`: Text, Nullable (Audit record of raw transcribed phrase)
- `created_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- `updated_at`: DateTime(timezone=True), Server Default `CURRENT_TIMESTAMP`
- Relationship: `customer`

### 3. Realtime Voice Streaming Protocol (WebSocket Scaffold)

Endpoint: `/api/v1/ws/voice`

Handshake Sequence:
1. Client connects via WebSocket (`ws://` or `wss://`).
2. Server accepts and issues `connection_ack` with `client_id` and timestamp.
3. Client can exchange `ping`/`pong` heartbeats to track network roundtrip latency.
4. Client sends `stream_init` with audio properties (e.g. `language: "hi-IN"`, `sample_rate: 16000`).
5. Server acknowledges with `stream_ready` and `session_id`, ready for audio frame streaming.
