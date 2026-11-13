# Judge Demo Checklist

## Before the demo

- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Production build passes
- [ ] Live Gnani credentials are available in the root `.env` if live STT/TTS is expected
- [ ] Demo customer exists in the database
- [ ] Audio input is permitted by the browser
- [ ] Browser volume and microphone are working

## During the demo

- [ ] Start from the dashboard and open the voice assistant
- [ ] Confirm the correct language is selected
- [ ] Speak a valid credit or payment phrase
- [ ] Check the proposed amount and projected balance
- [ ] Confirm or cancel explicitly
- [ ] Verify ledger update and spoken response

## Safety checks

- [ ] Duplicate confirmation is ignored
- [ ] Cancelled proposals do not commit
- [ ] Expired sessions reject stale confirmations
- [ ] New session does not reuse old idempotency state

## Sign-off

- [ ] Successful transaction shown in UI
- [ ] Final spoken confirmation played
- [ ] Balance reflects the expected amount
- [ ] No duplicate ledger rows created
