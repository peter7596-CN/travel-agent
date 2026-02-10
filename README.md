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

If `CONCUR_ACCESS_TOKEN` is not set, the app uses realistic mock responses for demos.

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

```bash
export CONCUR_BASE_URL="https://www.concursolutions.com"
export CONCUR_ACCESS_TOKEN="<oauth_access_token>"
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
