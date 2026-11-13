# VoxLedger AI — Project Status & Handoff Guide

## 1. Current Phase
**PHASE 2: Core Ledger Engine & Functional Dashboard** — **COMPLETED AND FULLY VERIFIED**

---

## 2. Architecture Decisions (Phase 1 & Phase 2)

1. **Fixed-Point Financial Calculation**:
   - Python `Decimal` and database column `Numeric(12, 2)` are strictly enforced across all models, schemas, and service functions.
   - Formula: $\text{Outstanding Balance} = \sum \text{CREDIT} - \sum \text{PAYMENT}$.
   - Floating-point calculations are prohibited to eliminate rounding drift in financial ledgers.

2. **Transaction Immutability & Reversals**:
   - Transactions support states: `COMPLETED` and `REVERSED`.
   - Financial records are never overwritten or deleted.
   - Idempotency is enforced using a unique `idempotency_key` (String 64) per transaction to prevent double-charging or duplicate entries on network retries.

3. **Customer Deletion Integrity**:
   - Deleting a customer with existing transaction history is blocked by foreign key constraint (`ondelete="RESTRICT"`) and pre-validated at the service layer, returning HTTP 409 (`CUSTOMER_HAS_TRANSACTIONS`).

4. **Payment Validation Rule**:
   - A customer payment cannot exceed their outstanding balance (`PAYMENT <= outstanding_balance`).
   - Zero or negative amounts are rejected with HTTP 422 (`amount > 0.00`).

5. **SQLite Alembic Migrations**:
   - Configured `render_as_batch=True` in `alembic/env.py` to allow SQLite table alter operations (e.g. dropping `NOT NULL` on `phone` and modifying constraints).

6. **Frontend UI/UX**:
   - Fintech styling with emerald green (`emerald-600`), midnight navy (`slate-900`), and warm ivory backgrounds.
   - Two-step transaction flow: Amount & details input -> explicit review & confirmation step displaying projected new balance before final submission.
   - Real-time client-side validation prevents submitting payments that exceed the customer's current balance.
   - Query invalidation ensures instant updates across customer lists, detail views, and dashboard KPI cards.

---

## 3. Files Created and Modified

### Phase 2 Backend (`backend/`)
- `app/models/customer.py` — Updated: `phone` made optional (`nullable=True`), `transactions` relationship updated with `RESTRICT` integrity.
- `app/models/transaction.py` — Updated: Added `status` (`TransactionStatus`: `COMPLETED`, `REVERSED`), `idempotency_key` (String(64), unique, indexed), `reversal_reason`, and `ForeignKey("customers.id", ondelete="RESTRICT")`.
- `alembic/versions/3c3db0ba7db1_phase_2_ledger_engine_schema_updates.py` — Applied migration using `batch_alter_table`.
- `app/schemas/customer.py` — Added `CustomerCreate`, `CustomerUpdate`, `CustomerResponse`, `CustomerSummaryResponse`, `CustomerListResponse`.
- `app/schemas/transaction.py` — Added `TransactionCreate`, `TransactionResponse`, `TransactionListResponse`.
- `app/schemas/dashboard.py` — Added `DashboardSummaryResponse`, `DashboardStats`.
- `app/services/ledger_service.py` — Core ledger engine: `get_customer_balance_stats()`, `record_transaction()` (with idempotency, balance checks, atomic commit), `get_dashboard_summary()` (live SQL aggregates).
- `app/api/v1/endpoints/customers.py` — Endpoints: `GET /customers`, `POST /customers`, `GET /customers/{id}`, `PATCH /customers/{id}`, `DELETE /customers/{id}`.
- `app/api/v1/endpoints/transactions.py` — Endpoints: `POST /transactions`, `GET /transactions`, `GET /transactions/{id}`, `GET /customers/{customer_id}/transactions`.
- `app/api/v1/endpoints/dashboard.py` — Endpoint: `GET /dashboard/summary`.
- `app/api/v1/router.py` — Registered all customer, transaction, and dashboard endpoint routers.
- `app/core/errors.py` — Updated Starlette error handler with `fastapi.encoders.jsonable_encoder` to cleanly serialize Decimal instances in validation errors.
- `tests/test_ledger_api.py` — Comprehensive integration tests covering customer CRUD, credit/payment calculations, payment > balance rejection, amount <= 0 rejection, customer deletion protection, idempotency deduplication, and dashboard calculations.
- `verify_live.py` — Updated live verification script to test live ledger calculations and dashboard summary over HTTP.

### Phase 2 Frontend (`frontend/`)
- `src/types/customer.ts` — TypeScript interfaces for Customer, CustomerSummary, CustomerListResponse.
- `src/types/transaction.ts` — TypeScript interfaces for Transaction, TransactionType, TransactionCreatePayload.
- `src/types/dashboard.ts` — TypeScript interfaces for DashboardSummary, DashboardStats.
- `src/services/customerService.ts` — API client integration for customer CRUD operations.
- `src/services/transactionService.ts` — API client integration for creating and listing transactions.
- `src/services/dashboardService.ts` — API client integration for dashboard summary.
- `src/components/ui/Modal.tsx` — Accessible modal dialog primitive with backdrop and escape key support.
- `src/components/ui/Input.tsx` — Form input field component with validation error styling.
- `src/components/ui/EmptyState.tsx` — Empty state placeholder component.
- `src/features/customers/AddCustomerModal.tsx` — Customer creation dialog with validation and automatic query invalidation.
- `src/features/transactions/TransactionModal.tsx` — Two-step transaction modal (Input -> Confirmation) with real-time balance validation, idempotency key generation, and credit/payment toggle.
- `src/features/dashboard/DashboardPage.tsx` — Full fintech dashboard with 4 KPI cards (Total Customers, Outstanding Credit, Today's Credit, Today's Payments), quick actions, and recent transaction feed.
- `src/features/customers/CustomerListPage.tsx` — Customer directory with real-time search, live balances, and quick credit/payment buttons.
- `src/features/customers/CustomerDetailPage.tsx` — Detailed customer view with 3 KPI cards, ledger timeline table, customer delete action, and credit/payment actions.
- `src/layouts/Header.tsx` & `MobileNav.tsx` — Updated navigation with links for Dashboard, Customers, Architecture, and API Docs.
- `src/app/router.tsx` — Configured routes for `/`, `/customers`, `/customers/:id`, and `/foundation`.
- `src/tests/App.test.tsx` — Updated tests for Phase 2 dashboard landing and navigation.
- `src/tests/AddCustomerModal.test.tsx` — Tests for customer registration and required name validation.
- `src/tests/TransactionModal.test.tsx` — Tests for credit modal, payment <= balance validation, step transitions, and amount > 0 checks.

---

## 4. Test Verification Records

### Backend Test Suite (Pytest)
```powershell
.\backend\venv\Scripts\python.exe -m pytest backend -v
```
**Outcome**: **18 passed, 0 failed in 5.62s (100% PASSING)**
- `test_errors.py`: 404 structured error
- `test_health.py`: unversioned health, versioned health, root endpoint
- `test_ledger_api.py`:
  - `test_create_and_retrieve_customer`
  - `test_search_customers`
  - `test_credit_and_payment_balance_calculation` (500 + 300 - 200 = 600)
  - `test_reject_zero_and_negative_amounts`
  - `test_reject_payment_exceeding_balance`
  - `test_reject_nonexistent_customer`
  - `test_customer_transaction_history`
  - `test_duplicate_submission_idempotency`
  - `test_dashboard_summary_calculations`
  - `test_customer_deletion_protection`
  - `test_concurrent_transaction_consistency`
- `test_models.py`:
  - `test_create_customer_and_transactions`
  - `test_customer_optional_phone_and_restrict_integrity`
- `test_websocket.py`: connection and handshake

### Frontend Test Suite (Vitest)
```powershell
npm test --prefix frontend
```
**Outcome**: **4 test files, 10 passed, 0 failed in 25.47s (100% PASSING)**
- `src/tests/AddCustomerModal.test.tsx` (2 tests passed)
- `src/tests/TransactionModal.test.tsx` (4 tests passed)
- `src/tests/App.test.tsx` (3 tests passed)
- `src/tests/HealthMetricsCard.test.tsx` (1 test passed)

### Frontend Production Build
```powershell
npm run build --prefix frontend
```
**Outcome**: **Clean compilation with zero TypeScript errors or warnings.**
- `dist/index.html` (0.59 kB)
- `dist/assets/index-CsJsvaMg.css` (26.48 kB)
- `dist/assets/index-D6FLq4T8.js` (335.64 kB)
- Built in 15.57s.

---

## 5. Known Errors and Resolutions

1. **Windows Python 3.14 Event Loop Socket Block**:
   - *Problem*: Windows sandbox blocks local loopback socket connections required by Python 3.14 `ProactorEventLoop._write_to_self()`.
   - *Fix*: Pytest and Uvicorn test runs must execute with `BypassSandbox: true`.

2. **SQLite ALTER TABLE Limitation**:
   - *Problem*: SQLite does not support direct `ALTER TABLE` to drop `NOT NULL` on existing columns.
   - *Fix*: Used `render_as_batch=True` in `alembic/env.py` and wrapped operations in `op.batch_alter_table` in migration `3c3db0ba7db1`.

3. **Starlette JSONResponse Decimal Serialization**:
   - *Problem*: FastAPI's `RequestValidationError.errors()` included `Decimal` instances which Starlette's `json.dumps()` could not serialize.
   - *Fix*: Encoded error details using `fastapi.encoders.jsonable_encoder(details)` in `create_error_response`.

4. **Deterministic Sort Order in SQLite Tests**:
   - *Problem*: Multiple transactions inserted within the same millisecond have identical timestamps, leading to non-deterministic ordering.
   - *Fix*: Added secondary sort key `Transaction.id.desc()` in `LedgerService.get_customer_transactions()` and `get_transactions()`.

---

## 6. Pending Tasks & Instructions for Next Phase (Phase 3)

Phase 2 is completely finished and verified. **Do not proceed to Phase 3 without explicit user approval.**

### Planned Phase 3 Scope:
1. **Gnani AI Integration**:
   - Multilingual voice streaming (Hindi, Hinglish, Tamil, Telugu, Kannada, Gujarati, Marathi, Bengali, English).
   - Audio capture via Web Audio API (16kHz 16-bit PCM).
   - Bidirectional WebSocket streaming to backend `/api/v1/ws/voice`.
   - Speech-to-Text (STT) transcription pipeline.
   - Voice intent classification & entity extraction (Customer name, Transaction Type, Amount).
   - Text-to-Speech (TTS) voice confirmation audio playback for shopkeepers.
2. **Shopkeeper Voice Interaction Flow**:
   - Shopkeeper speaks: *"Ramesh ko 250 rupaye ka udhar likho"*
   - Audio is streamed over WebSocket -> STT transcribes -> Intent extracted: Customer="Ramesh", Type="CREDIT", Amount="250.00".
   - Frontend shows confirmation modal / voice card -> Shopkeeper confirms -> Transaction recorded.
   - Audio response spoken back: *"Ramesh ke khate mein 250 rupaye udhar jode gaye. Kul baki 850 rupaye."*
