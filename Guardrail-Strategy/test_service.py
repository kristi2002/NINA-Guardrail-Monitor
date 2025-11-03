import pytest # type: ignore
import json
from unittest.mock import MagicMock, patch, Mock # type: ignore

# --- Setup ---
# Import the Flask app and other components we need to test
# We set env vars *before* importing to ensure app is configured for testing
import os
os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'mock-server:9092' # Use a fake server
os.environ['GUARDRAIL_ENABLE_PII_DETECTION'] = 'True'
os.environ['GUARDRAIL_ENABLE_TOXICITY_CHECK'] = 'True'

from app import app as flask_app
from kafka_producer import GuardrailKafkaProducer
from validators import GuardrailValidator
from kafka_handler import send_alert_to_kafka

# This is the "mock" object that will pretend to be the guardrails-ai validation result
class MockValidationOutcome:
    def __init__(self, outcome, validated_output=None, error_message=None):
        self.outcome = outcome
        self.validated_output = validated_output
        self.error_message = error_message

# --- Fixtures (Test Setup) ---

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    flask_app.config.update({"TESTING": True})
    yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_kafka_producer():
    """Mocks the KafkaProducer to prevent real network calls."""
    with patch.object(GuardrailKafkaProducer, 'connect', return_value=None), \
         patch.object(GuardrailKafkaProducer, 'send_guardrail_event', return_value=True) as mock_send:
        yield mock_send

@pytest.fixture
def mock_guard_validate():
    """Mocks the 'guard.validate' method inside the GuardrailValidator."""
    # Create a mock guard object with a validate method
    mock_guard = MagicMock()
    mock_validate = MagicMock()
    mock_guard.validate = mock_validate
    
    # Patch the guard attribute on the validator instance (not class)
    # We need to patch it on the singleton instance in app.py
    with patch.object(flask_app.validator, 'guard', mock_guard):
        yield mock_validate

# --- Test Cases ---

## 1. API Endpoint Tests (app.py)

def test_health_check(client):
    """Test the /health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['kafka'] == 'disconnected' # Expected since we mock connection
    assert data['validator']['toxicity_enabled'] == True

def test_validate_clean_message(client, mock_guard_validate, mock_kafka_producer):
    """Test the /validate endpoint with a clean message."""
    
    # --- Arrange ---
    # Tell the mock guard to return a "pass" result
    clean_message = "This is a clean message."
    mock_guard_validate.return_value = MockValidationOutcome(
        outcome='pass',
        validated_output=clean_message
    )
    
    payload = {
        "conversation_id": "conv-test-123",
        "message": clean_message
    }

    # --- Act ---
    response = client.post('/validate', data=json.dumps(payload), content_type='application/json')
    data = response.get_json()

    # --- Assert ---
    assert response.status_code == 200
    assert data['valid'] == True
    assert data['event']['event_type'] == 'validation_passed'
    assert data['event']['kafka_sent'] == False  # No Kafka event for passed validations
    
    # Check that NO event was sent to Kafka (passed events are no longer sent)
    mock_kafka_producer.assert_not_called()

def test_validate_failed_message(client, mock_guard_validate):
    """Test the /validate endpoint with a failed (toxic) message.
    
    This test checks that the API endpoint correctly *reports* a failure
    when the underlying validator service returns a 'fail' outcome.
    """
    
    # --- Arrange ---
    # Tell the mock guard to return a "fail" result
    toxic_message = "This is a toxic message."
    mock_guard_validate.return_value = MockValidationOutcome(
        outcome='fail',
        error_message="Toxic message detected"
    )
    
    payload = {
        "conversation_id": "conv-test-456",
        "message": toxic_message
    }

    # --- Act ---
    response = client.post('/validate', data=json.dumps(payload), content_type='application/json')
    data = response.get_json()

    # --- Assert ---
    assert response.status_code == 200
    assert data['valid'] == False
    assert data['event']['event_type'] == 'validation_failed'
    
    # This is the key check for your app.py logic:
    # 'kafka_sent': not validation_results['valid']
    # Since 'valid' is False, 'kafka_sent' should be True.
    assert data['event']['kafka_sent'] == True

def test_validate_missing_message(client):
    """Test the /validate endpoint with a bad request (missing 'message')."""
    payload = {"conversation_id": "conv-test-789"} # Missing 'message'
    response = client.post('/validate', data=json.dumps(payload), content_type='application/json')
    data = response.get_json()

    assert response.status_code == 400
    assert 'error' in data
    assert data['error'] == "Missing required field: message"

## 2. Kafka Handler Test (kafka_handler.py)

def test_kafka_handler_sends_message():
    """Test that the 'send_alert_to_kafka' function formats and sends a message."""
    
    # --- Arrange ---
    # Mock the dependencies *inside* kafka_handler.py
    mock_producer = MagicMock()
    mock_producer.send_guardrail_event.return_value = True
    
    # Create fake validation failure data
    mock_fail_result = MagicMock()
    mock_fail_result.error_message = "PII detected"
    mock_fail_result.validator.__class__.__name__ = "DetectPII"
    
    with patch('kafka_handler.get_kafka_producer', return_value=mock_producer):
        # --- Act ---
        send_alert_to_kafka(
            value="my email is test@example.com",
            fail_result=mock_fail_result,
            metadata={"conversation_id": "conv-pii-test"}
        )

        # --- Assert --- # type: ignore
        # Check that the producer's 'send' method was called
        mock_producer.send_guardrail_event.assert_called_once()
        
        # Check the contents of the message it tried to send
        sent_conversation_id = mock_producer.send_guardrail_event.call_args[0][0]
        sent_event = mock_producer.send_guardrail_event.call_args[0][1]
        
        assert sent_conversation_id == "conv-pii-test"
        assert sent_event['event_type'] == "privacy_violation_prevented"
        assert sent_event['severity'] == "high"
        assert "PII detected" in sent_event['message']