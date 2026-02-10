from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import parse, request


@dataclass
class ConcurConfig:
    base_url: str = "https://www.concursolutions.com"
    access_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None
    token_url: str = "https://us2.api.concursolutions.com/oauth2/v0/token"


class ConcurClient:
    """SAP Concur wrapper with OAuth and local mock fallback."""

    def __init__(self, config: ConcurConfig) -> None:
        self.config = config
        self._token_cache: str | None = config.access_token
        self._token_expiry_epoch: float = 0.0

    def get_traveler_profile(self, traveler_email: str) -> dict[str, Any]:
        if self._use_mock_mode():
            return {
                "email": traveler_email,
                "name": "Executive Traveler",
                "home_airport": "SFO",
                "seat_preference": "Aisle",
                "known_visa_status": {"Schengen": "valid", "US": "citizen"},
            }

        query = parse.urlencode({"email": traveler_email})
        url = f"{self.config.base_url}/api/travelprofile/v1.0/profile?{query}"
        return self._request_json("GET", url)

    def create_trip_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._use_mock_mode():
            return {"trip_request_id": "MOCK-REQ-1001", "status": "submitted", "payload": payload}

        url = f"{self.config.base_url}/api/travelrequest/v4/requests"
        return self._request_json("POST", url, payload)

    def get_itinerary(self, trip_request_id: str) -> dict[str, Any]:
        if self._use_mock_mode():
            return {
                "trip_request_id": trip_request_id,
                "segments": [
                    {
                        "type": "flight",
                        "from": "SFO",
                        "to": "LHR",
                        "depart_local": "2026-04-02T19:20",
                        "arrive_local": "2026-04-03T13:40",
                        "flight_number": "BA286",
                        "seat": "14C",
                    },
                    {"type": "hotel", "name": "Canary Riverside", "check_in": "2026-04-03", "check_out": "2026-04-07"},
                ],
                "booking_confirmed": True,
            }

        url = f"{self.config.base_url}/api/travelrequest/v4/requests/{trip_request_id}"
        return self._request_json("GET", url)

    def _use_mock_mode(self) -> bool:
        return not any([self.config.access_token, self.config.refresh_token])

    def _get_access_token(self) -> str:
        if self._token_cache and time.time() < self._token_expiry_epoch:
            return self._token_cache
        if self._token_cache and not self.config.refresh_token:
            return self._token_cache

        if not all([self.config.client_id, self.config.client_secret, self.config.refresh_token]):
            raise RuntimeError(
                "Concur API credentials incomplete. Provide CONCUR_ACCESS_TOKEN or OAuth values "
                "(CONCUR_CLIENT_ID, CONCUR_CLIENT_SECRET, CONCUR_REFRESH_TOKEN)."
            )

        payload = parse.urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "refresh_token": self.config.refresh_token,
            }
        ).encode("utf-8")
        req = request.Request(
            self.config.token_url,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=payload,
        )
        with request.urlopen(req, timeout=20) as response:
            token_payload = json.loads(response.read().decode("utf-8"))

        token = token_payload.get("access_token")
        expires_in = int(token_payload.get("expires_in", 3600))
        if not token:
            raise RuntimeError("Concur OAuth token endpoint returned no access_token.")

        self._token_cache = token
        self._token_expiry_epoch = time.time() + max(expires_in - 60, 60)
        return token

    def _request_json(self, method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url, method=method, headers=headers, data=data)
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
