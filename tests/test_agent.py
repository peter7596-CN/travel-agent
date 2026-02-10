from app.agent import ConversationState, TravelWorkflowAgent
from app.concur_client import ConcurClient, ConcurConfig


def test_workflow_can_create_trip_request():
    agent = TravelWorkflowAgent(ConcurClient(ConcurConfig()))
    state = ConversationState()

    first = agent.respond("start new trip for ceo@example.com to london", state)
    assert first["stage"] == "Travel need identified"
    assert "ceo@example.com" in first["assistant_message"]

    second = agent.respond("next", state)
    assert second["stage"] == "Travel request creation"
    assert state.trip_request_id is not None


def test_visa_stage_responds_to_flags():
    agent = TravelWorkflowAgent(ConcurClient(ConcurConfig()))
    state = ConversationState(stage_index=3)

    response = agent.respond("passport expires 2028-01-01 and need visa", state)
    assert response["stage"] == "Visa & passport checks"
    assert "2028-01-01" in response["assistant_message"]
    assert "visa needed" in response["assistant_message"]


def test_show_checklist_reflects_collected_fields():
    agent = TravelWorkflowAgent(ConcurClient(ConcurConfig()))
    state = ConversationState()

    first = agent.respond("show checklist", state)
    assert "⬜ traveler email" in first["assistant_message"]

    agent.respond("start new trip for ceo@example.com to london", state)
    second = agent.respond("show checklist", state)
    assert "✅ traveler email" in second["assistant_message"]
    assert "✅ destination" in second["assistant_message"]
