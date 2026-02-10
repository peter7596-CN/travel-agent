from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import parse, request


@dataclass
class ConcurConfig:
    base_url: str = "https://www.concursolutions.com"
    access_token: str | None = None


class ConcurClient:
    """SAP Concur wrapper with local mock fallback."""

    def __init__(self, config: ConcurConfig) -> None:
        self.config = config

    def get_traveler_profile(self, traveler_email: str) -> dict[str, Any]:
        if not self.config.access_token:
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
        if not self.config.access_token:
            return {"trip_request_id": "MOCK-REQ-1001", "status": "submitted", "payload": payload}

        url = f"{self.config.base_url}/api/travelrequest/v4/requests"
        return self._request_json("POST", url, payload)

    def get_itinerary(self, trip_request_id: str) -> dict[str, Any]:
        if not self.config.access_token:
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

    def _request_json(self, method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.config.access_token}", "Content-Type": "application/json"}
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url, method=method, headers=headers, data=data)
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
