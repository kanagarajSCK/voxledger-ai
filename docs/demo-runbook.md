# Demo Runbook

## Entry conditions

- Backend dependencies installed
- Frontend dependencies installed
- Project root `.env` contains the required Gnani credentials if live provider verification is intended
- The SQLite database is ready

## Backend validation

```bash
cd D:\Projects\voxledger-ai\backend
pytest -q tests/test_voice_workflow.py
pytest -q
python verify_gnani_live.py
```

## Frontend validation

```bash
cd D:\Projects\voxledger-ai\frontend
npm test -- --run
npm run build
```

## Demo flow

1. Open the frontend app and sign in or navigate to the dashboard.
2. Use the floating voice button.
3. Say a purchase or credit statement with a customer name and amount.
4. Review the proposed transaction and projected balance.
5. Confirm with a clear confirmation phrase like "Yes".
6. Verify the ledger update and spoken confirmation.

## Safety notes

- Confirmations are session-scoped and stale actions are rejected.
- Replays do not write a duplicate transaction.
- Cancelled actions cannot be executed later.
- The live provider path must never be used without secret protection.
