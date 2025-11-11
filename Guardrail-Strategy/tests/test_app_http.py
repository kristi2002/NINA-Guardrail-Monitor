import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
for path in (PROJECT_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture
def client(monkeypatch):
    from app import app, validator

    dummy_result = {
        "valid": False,
        "violations": [
            {
                "type": "validation_failed",
                "severity": "medium",
                "details": {"error_message": "Simulated failure"},
            }
        ],
        "response_time_ms": 12,
    }

    def fake_validate(message, conversation_id, user_id=None, conversation_history=None, **kwargs):
        assert message == "Patient asked for dosage details."
        assert conversation_id == "conv-http-1"
        assert user_id == "user-42"
        return dummy_result

    monkeypatch.setattr(validator, "validate", fake_validate)

    return app.test_client()


def test_validate_endpoint_handles_agent_payload(client):
    payload = {
        "message": "Patient asked for dosage details.",
        "conversation_id": "conv-http-1",
        "user_id": "user-42",
        "metadata": {"tenant": "clinic-a"},
    }

    response = client.post(
        "/validate",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["conversation_id"] == "conv-http-1"
    assert body["validation_results"]["valid"] is False
    assert body["validation_results"]["violations"][0]["type"] == "validation_failed"

