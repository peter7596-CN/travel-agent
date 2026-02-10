# Executive Travel Agent (SAP Concur Connected Chatbot)

This project is a runnable chatbot app that implements the end-to-end executive travel workflow from your requirement image, with SAP Concur integration points.

## Features implemented

The bot orchestrates all requested stages:
1. Travel need identified (auto pre-fill)
2. Travel request creation (submit to Concur)
3. Itinerary review (find issues + correction draft)
4. Visa & passport checks
5. Visa form automation (+ vaccination reminder logic point)
6. Booking confirmation monitor
7. Transfer checks (airport ↔ hotel ↔ office ↔ meeting)
8. Build final itinerary (local/base time context)
9. Itinerary diary confirmation (calendar invite details)
10. Trip preparation packaging for meeting context

## SAP Concur connectivity

`app/concur_client.py` contains real API call paths and auth headers for:
- traveler profile
- travel request creation
- itinerary retrieval

If neither `CONCUR_ACCESS_TOKEN` nor `CONCUR_REFRESH_TOKEN` is set, the app uses realistic mock responses for demos.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
python -m app.server
```

Open: `http://localhost:8000`

## Configure Concur API

Use either direct bearer token mode:

```bash
export CONCUR_BASE_URL="https://www.concursolutions.com"
export CONCUR_ACCESS_TOKEN="<oauth_access_token>"
python -m app.server
```

Or OAuth refresh-token mode (recommended for long-running deployments):

```bash
export CONCUR_BASE_URL="https://www.concursolutions.com"
export CONCUR_CLIENT_ID="<concur_client_id>"
export CONCUR_CLIENT_SECRET="<concur_client_secret>"
export CONCUR_REFRESH_TOKEN="<concur_refresh_token>"
# Optional override if your tenant uses a different auth host
export CONCUR_TOKEN_URL="https://us2.api.concursolutions.com/oauth2/v0/token"
python -m app.server
```

## API

- `GET /api/health`
- `POST /api/chat`

Request body example:

```json
{
  "session_id": "exec-ea-1",
  "message": "start new trip for ceo@example.com to london"
}
```

Useful chat commands:
- `start new trip for <email> to <city>`
- `next`
- `show checklist` (progress snapshot of key fields)

## Tests

```bash
pytest
```
