# Privacy and Data Handling

## Data in scope

- Customer names, phone numbers, and transaction values
- Audio captured from the microphone
- Transcript text from the live STT service
- Ledger records and session state

## Handling rules

- The backend is the only service that reads and writes financial records.
- API keys and provider secrets are stored in the project root `.env` file and never exposed to frontend code or logs.
- Audio and transcript data should be treated as sensitive business data and retained only as needed for demo or troubleshooting.
- The live provider acceptance script must not print the secret values or include them in commits or logs.

## Operational guidance

- Use the `.env` file locally only; do not commit secrets to source control.
- Log only a redacted or generic status rather than raw transcript data in production or demo environments.
- Keep customer ledger data limited to the local demo database unless the production environment is explicitly approved.
