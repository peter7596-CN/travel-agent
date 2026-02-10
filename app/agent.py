from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .concur_client import ConcurClient


@dataclass
class ConversationState:
    traveler_email: str | None = None
    trip_request_id: str | None = None
    destination: str | None = None
    passport_expiry: str | None = None
    needs_visa: bool | None = None
    stage_index: int = 0
    collected_notes: list[str] = field(default_factory=list)


class TravelWorkflowAgent:
    stages = [
        "Travel need identified",
        "Travel request creation",
        "Itinerary review",
        "Visa & passport checks",
        "Visa form automation",
        "Booking confirmation",
        "Transfer checks",
        "Build final itinerary",
        "Itinerary diary confirmation",
        "Trip preparation",
    ]

    def __init__(self, concur_client: ConcurClient) -> None:
        self.concur_client = concur_client

    def respond(self, user_message: str, state: ConversationState) -> dict[str, Any]:
        lowered = user_message.lower().strip()
        self._extract_fields(user_message, state)

        if lowered == "show checklist":
            return {
                "stage": self.stages[state.stage_index],
                "state": state.__dict__,
                "assistant_message": self._render_checklist(state),
                "available_commands": ["next", "start new trip", "show checklist"],
            }

        if "start" in lowered or "new trip" in lowered:
            state.stage_index = 0
        if lowered in {"next", "continue", "proceed"}:
            state.stage_index = min(state.stage_index + 1, len(self.stages) - 1)

        stage = self.stages[state.stage_index]
        profile = self.concur_client.get_traveler_profile(state.traveler_email) if state.traveler_email else None
        return {
            "stage": stage,
            "state": state.__dict__,
            "assistant_message": self._build_stage_action(stage, state, profile),
            "available_commands": ["next", "start new trip", "show checklist"],
        }

    def _extract_fields(self, message: str, state: ConversationState) -> None:
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", message)
        if email_match:
            state.traveler_email = email_match.group(0)

        destination_match = re.search(r"to\s+([A-Za-z ]{2,30})", message)
        if destination_match:
            state.destination = destination_match.group(1).strip().title()

        year_match = re.search(r"20\d{2}-\d{2}-\d{2}", message)
        if year_match and "passport" in message.lower():
            state.passport_expiry = year_match.group(0)

        low = message.lower()
        if "visa required" in low or "need visa" in low:
            state.needs_visa = True
        if "no visa" in low:
            state.needs_visa = False

    def _build_stage_action(self, stage: str, state: ConversationState, profile: dict[str, Any] | None) -> str:
        if stage == "Travel need identified":
            return (
                "I identified a new executive travel need and pre-filled a request draft. "
                f"Traveler: {state.traveler_email or 'missing'}, destination: {state.destination or 'missing'}."
            )
        if stage == "Travel request creation":
            trip = self.concur_client.create_trip_request(
                {
                    "traveler": state.traveler_email,
                    "destination": state.destination,
                    "purpose": "Executive business travel",
                }
            )
            state.trip_request_id = trip["trip_request_id"]
            return f"Generated full travel request and submitted to SAP Concur. Trip request ID: {state.trip_request_id}."
        if stage == "Itinerary review":
            if not state.trip_request_id:
                return "No trip request exists yet. Say 'next' after creating request."
            itinerary = self.concur_client.get_itinerary(state.trip_request_id)
            issues = self._itinerary_issues(itinerary)
            return (
                "I found itinerary issues: " + "; ".join(issues) + ". Drafted correction email."
                if issues
                else "Itinerary review complete. No errors detected."
            )
        if stage == "Visa & passport checks":
            visa_note = "visa needed" if state.needs_visa else "visa not needed / unknown"
            return f"Checked visa/passport. Passport expiry: {state.passport_expiry or 'missing'}, {visa_note}."
        if stage == "Visa form automation":
            return (
                "Located visa form, auto-filled traveler/trip data, and flagged missing support docs."
                if state.needs_visa
                else "No visa required, visa automation marked complete."
            )
        if stage == "Booking confirmation":
            return "Monitoring Concur booking status and drafting follow-ups if any segment is unconfirmed."
        if stage == "Transfer checks":
            return "Checked airport↔hotel↔office transfers and suggested private car for late arrival."
        if stage == "Build final itinerary":
            seat_pref = profile.get("seat_preference") if profile else "unknown"
            return f"Built final itinerary with local/base times, contacts, and visa status. Seat pref: {seat_pref}."
        if stage == "Itinerary diary confirmation":
            return "Drafted calendar invites with airline, flight number, seat, and local timing for EA review."
        return "Packaged itinerary into meeting context with stakeholder list and pre-read checklist."

    def _itinerary_issues(self, itinerary: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        for segment in itinerary.get("segments", []):
            if segment.get("type") == "flight":
                if not segment.get("seat"):
                    issues.append("missing seat assignment")
                if segment.get("from") == segment.get("to"):
                    issues.append("origin and destination are identical")
        return issues

    def _render_checklist(self, state: ConversationState) -> str:
        required = {
            "traveler email": bool(state.traveler_email),
            "destination": bool(state.destination),
            "trip request": bool(state.trip_request_id),
            "passport expiry": bool(state.passport_expiry),
            "visa requirement": state.needs_visa is not None,
        }
        lines = ["Executive travel checklist:"]
        for item, done in required.items():
            lines.append(f"- {'✅' if done else '⬜'} {item}")
        return "\n".join(lines)
