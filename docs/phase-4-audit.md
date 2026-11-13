# Phase 4 Audit

## Scope checked

- Financial safety in the voice workflow service
- Corrected proposal amount commit logic
- Duplicate confirmation idempotency
- Cancellation replay blocking
- Expired-session stale-confirmation rejection
- New-session isolation for idempotency state
- Backend unit and integration suite
- Frontend automated suite and production build
- Live Gnani STT/TTS acceptance path when credentials are present

## Verified results

- `backend/tests/test_voice_workflow.py`: 8 passed
- `pytest -q`: 38 passed
- `frontend` Vitest suite: 15 passed
- `frontend` production build: passed
- Live Gnani script: passed after fixing the environment loader for the project-root `.env` and replacing Windows-unfriendly currency characters in the verification output

## What is genuine

- The backend flow resolves customer names, creates pending actions, enforces confirmation and cancellation, and writes ledger transactions through the ledger service.
- The correction flow invalidates the previous action identity and creates a new action idempotency key.
- Replayed confirmations are treated as the same action rather than creating a second ledger row.
- Expired sessions reject stale confirmation attempts.
- New sessions start clean and cannot reuse old pending-action state.

## What is mocked

- Frontend component tests simulate UI behavior, not real microphone capture.
- Browser-side permission flows and mic activation are not exercised by Selenium/Playwright in this repo.
- The live provider path is real when credentials are present; without credentials it remains blocked by configuration rather than business logic.

## Remaining manual checks

- Real browser microphone permission flow in Safari/Chrome on desktop and Android
- Full voice UX against the live provider in a demo environment
- Optional browser E2E if Playwright is added later

## Root-cause fix found during validation

- The backend settings loader was reading only `backend/.env` instead of the project root `.env`, which prevented the live Gnani acceptance script from seeing credentials even though a valid project-root `.env` existed.
- The verification script also printed the rupee symbol in a Windows code-page that cannot encode it, which caused a crash before the final pass message.
- Both issues were fixed without altering the app logic itself.
