#!/usr/bin/env python3
"""
Guardrail Service - System 2: The Guard
Flask microservice for guardrail validation (port 5001)
"""

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import logging
import uuid
from datetime import datetime
from validators import GuardrailValidator
from kafka_producer import GuardrailKafkaProducer

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
PORT = int(os.getenv('PORT', 5001))
SERVICE_NAME = os.getenv('SERVICE_NAME', 'guardrail-service')

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
validator = GuardrailValidator()
kafka_producer = GuardrailKafkaProducer()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    kafka_status = 'connected' if kafka_producer.producer else 'disconnected'
    
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'port': PORT,
        'kafka': kafka_status,
        'validator': {
            'pii_enabled': validator.enable_pii_detection,
            'toxicity_enabled': validator.enable_toxicity_check,
            'compliance_enabled': validator.enable_compliance_check
        }
    }), 200

@app.route('/validate', methods=['POST'])
def validate_message():
    """Validate a message against guardrails"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing required field: message'
            }), 400
        
        message = data['message']
        conversation_id = data.get('conversation_id', f'conv_{uuid.uuid4().hex[:8]}')
        user_id = data.get('user_id', f'user_{conversation_id.split("_")[-1] if "_" in conversation_id else "unknown"}')
        
        logger.info(f"Validating message for conversation: {conversation_id}")
        
        # Validate message
        validation_results = validator.validate(message, conversation_id)
        
        # Determine event type and severity based on validation results
        event_type = 'validation_passed'
        severity = 'info'
        
        if not validation_results['valid']:
            # Determine severity based on violations
            max_severity = 'low'
            for violation in validation_results['violations']:
                viol_severity = violation.get('severity', 'low')
                severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                if severity_order.get(viol_severity, 0) > severity_order.get(max_severity, 0):
                    max_severity = viol_severity
            
            severity = max_severity
            
            # Determine event type based on violation types
            violation_types = [v.get('type') for v in validation_results['violations']]
            if 'pii_detection' in violation_types:
                event_type = 'privacy_violation_prevented'
            elif 'toxicity' in violation_types:
                event_type = 'inappropriate_content'
            elif 'compliance' in violation_types:
                event_type = 'compliance_violation'
            else:
                event_type = 'guardrail_triggered'
        
        # Prepare guardrail event for Kafka
        guardrail_event = {
            'schema_version': '1.0',
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'severity': severity,
            'message': f"Message validation {'passed' if validation_results['valid'] else 'failed'}",
            'context': message[:200] + '...' if len(message) > 200 else message,  # Truncate for context
            'user_id': user_id,
            'action_taken': 'allowed' if validation_results['valid'] else 'logged',
            'confidence_score': 0.95 if validation_results['valid'] else 0.85,
            'guardrail_version': '2.0',
            'response_time_ms': validation_results.get('response_time_ms', 0),
            'validation_results': validation_results,
            'session_metadata': {
                'validation_timestamp': validation_results.get('validation_timestamp', datetime.now().isoformat()),
                'message_length': len(message)
            }
        }
        
        # Send event to Kafka
        kafka_sent = False
        if kafka_producer.producer:
            try:
                kafka_sent = kafka_producer.send_guardrail_event(conversation_id, guardrail_event)
                if kafka_sent:
                    logger.info(f"Guardrail event sent to Kafka for conversation {conversation_id}")
                else:
                    logger.warning(f"Failed to send guardrail event to Kafka for conversation {conversation_id}")
            except Exception as kafka_error:
                logger.error(f"Kafka error: {kafka_error}", exc_info=True)
        
        # Prepare response
        response = {
            'success': True,
            'valid': validation_results['valid'],
            'conversation_id': conversation_id,
            'validation_results': validation_results,
            'event': {
                'event_type': event_type,
                'severity': severity,
                'kafka_sent': kafka_sent
            }
        }
        
        # Return appropriate status code based on validation result
        status_code = 200 if validation_results['valid'] else 200  # Still 200, but include violation info
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error validating message: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/validate/batch', methods=['POST'])
def validate_batch():
    """Validate multiple messages in batch"""
    try:
        data = request.get_json()
        
        if not data or 'messages' not in data:
            return jsonify({
                'error': 'Missing required field: messages (array)'
            }), 400
        
        messages = data['messages']
        conversation_id = data.get('conversation_id', f'conv_{uuid.uuid4().hex[:8]}')
        user_id = data.get('user_id', f'user_{conversation_id.split("_")[-1] if "_" in conversation_id else "unknown"}')
        
        if not isinstance(messages, list):
            return jsonify({
                'error': 'messages must be an array'
            }), 400
        
        results = []
        for idx, message_data in enumerate(messages):
            if isinstance(message_data, str):
                message = message_data
            elif isinstance(message_data, dict) and 'message' in message_data:
                message = message_data['message']
            else:
                continue
            
            validation_results = validator.validate(message, conversation_id)
            results.append({
                'index': idx,
                'message': message[:100] + '...' if len(message) > 100 else message,
                'validation': validation_results
            })
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'processed_count': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating batch: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} on port {PORT}")
    logger.info(f"Kafka bootstrap servers: {kafka_producer.bootstrap_servers}")
    logger.info(f"Validator settings - PII: {validator.enable_pii_detection}, "
                f"Toxicity: {validator.enable_toxicity_check}, "
                f"Compliance: {validator.enable_compliance_check}")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')
    except KeyboardInterrupt:
        logger.info("Shutting down guardrail service...")
        kafka_producer.close()
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        kafka_producer.close()

