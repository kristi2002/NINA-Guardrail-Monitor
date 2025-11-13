#!/usr/bin/env python3
"""
Guardrail Service - System 2: The Guard
Flask microservice for guardrail validation (port 5001)
"""

import os
import sys
from pathlib import Path
import logging
import uuid
from datetime import datetime, timezone

# Ensure repo root is on path for shared packages before local imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flask import Flask, request, jsonify
from dotenv import load_dotenv 
from services.validation import GuardrailValidator
from services.infrastructure.kafka import GuardrailKafkaProducer, GuardrailKafkaConsumer, OperatorActionsConsumer

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
PORT = int(os.getenv('PORT', 5001))
SERVICE_NAME = os.getenv('SERVICE_NAME', 'guardrail-service')
SERVICE_START_TIME = datetime.now(timezone.utc)

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
validator = GuardrailValidator()

# Get feedback learner from consumer if available (for validator to use)
feedback_learner = None

# Initialize Kafka producer (will try to connect but won't fail if unavailable)
try:
    kafka_producer = GuardrailKafkaProducer()
    if not kafka_producer.producer:
        logger.warning("⚠️ Kafka producer initialized but not connected. Service will continue without Kafka.")
except Exception as e:
    logger.error(f"Failed to initialize Kafka producer: {e}", exc_info=True)
    # Create a dummy producer object to prevent errors
    class DummyProducer:
        producer = None
        bootstrap_servers = "unavailable"
        def send_guardrail_event(self, *args, **kwargs):
            return False
        def close(self):
            pass
    kafka_producer = DummyProducer()

# Initialize feedback learner independently (doesn't require Kafka)
try:
    from services.learning.feedback_learner import FeedbackLearner
    feedback_learner = FeedbackLearner()
    validator.set_feedback_learner(feedback_learner)
    logger.info("✅ Feedback learner initialized - adaptive learning enabled")
except Exception as e:
    logger.warning(f"⚠️ Failed to initialize feedback learner: {e}. Analytics will not be available.", exc_info=True)
    feedback_learner = None

# Initialize Kafka consumer for guardrail_control feedback (will try to connect but won't fail if unavailable)
kafka_consumer = None
try:
    # Pass the feedback learner to the consumer so they share the same instance
    kafka_consumer = GuardrailKafkaConsumer()
    # Use our global feedback learner if available, otherwise use the consumer's
    if feedback_learner:
        kafka_consumer.feedback_learner = feedback_learner
        logger.info("✅ Kafka consumer using global feedback learner instance")
    elif kafka_consumer.feedback_learner:
        feedback_learner = kafka_consumer.feedback_learner
        validator.set_feedback_learner(feedback_learner)
        logger.info("✅ Feedback learner initialized from Kafka consumer")
    
    # Start consumer in background (will handle connection failures gracefully)
    consumer_started = kafka_consumer.start()
    if not consumer_started:
        logger.warning("⚠️ Kafka consumer not started (Kafka may be unavailable). Service will continue without real-time feedback consumption.")
        logger.info("ℹ️ Feedback learner is still available for analytics and persisted data")
    else:
        logger.info("✅ Kafka consumer started - real-time feedback enabled")
except Exception as e:
    logger.warning(f"⚠️ Failed to initialize Kafka consumer: {e}. Service will continue without real-time feedback consumption.", exc_info=True)
    kafka_consumer = None
    if feedback_learner:
        logger.info("ℹ️ Feedback learner is still available for analytics and persisted data")

# Initialize Kafka consumer for operator_actions (just logs events for evidence tracking)
operator_actions_consumer = None
try:
    operator_actions_consumer = OperatorActionsConsumer()
    # Start consumer in background (will handle connection failures gracefully)
    operator_consumer_started = operator_actions_consumer.start()
    if not operator_consumer_started:
        logger.warning("⚠️ Operator actions consumer not started (Kafka may be unavailable). Service will continue without operator actions logging.")
    else:
        logger.info("✅ Operator actions consumer started - operator actions will be logged for evidence tracking")
except Exception as e:
    logger.warning(f"⚠️ Failed to initialize operator actions consumer: {e}. Service will continue without operator actions logging.", exc_info=True)
    operator_actions_consumer = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    kafka_producer_status = 'connected' if kafka_producer.producer else 'disconnected'
    kafka_consumer_status = 'running' if (kafka_consumer and kafka_consumer.is_running()) else 'stopped'
    operator_actions_consumer_status = 'running' if (operator_actions_consumer and operator_actions_consumer.is_running()) else 'stopped'
    kafka_status = 'connected' if (kafka_producer.producer or (kafka_consumer and kafka_consumer.is_running()) or (operator_actions_consumer and operator_actions_consumer.is_running())) else 'disconnected'
    
    feedback_stats = kafka_consumer.get_feedback_stats() if kafka_consumer else {}
    operator_actions_stats = operator_actions_consumer.get_statistics() if operator_actions_consumer else {}
    
    # Get adaptive learning stats
    adaptive_learning = {'enabled': False}
    if feedback_learner:
        adaptive_learning = {
            'enabled': True,
            'threshold_adjustments': feedback_learner.threshold_adjustments.copy(),
            'problematic_rules': feedback_learner.get_problematic_rules()[:5],  # Top 5
            'statistics': feedback_learner.get_statistics()
        }
    
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'port': PORT,
        'kafka': {
            'status': kafka_status,
            'producer': kafka_producer_status,
            'consumer': kafka_consumer_status,
            'operator_actions_consumer': operator_actions_consumer_status,
            'control_topic': os.getenv('KAFKA_TOPIC_CONTROL', 'guardrail_control'),
            'operator_actions_topic': os.getenv('KAFKA_TOPIC_OPERATOR', 'operator_actions')
        },
        'operator_actions': operator_actions_stats,
        'validator': {
            'pii_enabled': validator.enable_pii_detection,
            'toxicity_enabled': validator.enable_toxicity_check,
            'compliance_enabled': validator.enable_compliance_check,
            'llm_context_check_enabled': validator.enable_llm_context_check,
            'llm_available': validator.openai_client is not None
        },
        'feedback': feedback_stats,
        'adaptive_learning': adaptive_learning
    }), 200

@app.route('/analytics/performance', methods=['GET'])
def get_guardrail_performance():
    """Get guardrail performance analytics including feedback statistics"""
    try:
        if not feedback_learner:
            return jsonify({
                'success': False,
                'error': 'Feedback learner not available',
                'message': 'Adaptive learning is not enabled'
            }), 503
        
        stats = feedback_learner.get_statistics()
        problematic_rules = feedback_learner.get_problematic_rules()
        timeline = feedback_learner.get_feedback_timeline(days=7)
        recent_feedback = feedback_learner.get_recent_feedback(limit=5)
        last_feedback_at = feedback_learner.get_last_feedback_timestamp()
        
        # Get performance metrics for each rule
        rule_performance = {}
        for rule_name in feedback_learner.rule_statistics.keys():
            rule_performance[rule_name] = feedback_learner.get_rule_performance(rule_name)

        uptime_seconds = max(
            0,
            int((datetime.now(timezone.utc) - SERVICE_START_TIME).total_seconds()),
        )

        trend_summary = {
            'window_days': len(timeline),
            'false_alarms': sum(item['false_alarms'] for item in timeline),
            'true_positives': sum(item['true_positives'] for item in timeline),
            'total_feedback': sum(item['total_feedback'] for item in timeline),
        }
        total_feedback_window = trend_summary['total_feedback']
        trend_summary['accuracy'] = (
            trend_summary['true_positives'] / total_feedback_window
            if total_feedback_window > 0 else 0.0
        )
        
        return jsonify({
            'success': True,
            'data': {
                'available': True,  # Explicitly mark as available
                'service': SERVICE_NAME,
                'telemetry_version': 1,
                'uptime_seconds': uptime_seconds,
                'last_feedback_at': last_feedback_at,
                'overview': {
                    'total_feedback': stats['total_feedback'],
                    'false_alarms': stats['false_alarms'],
                    'true_positives': stats['true_positives'],
                    'false_alarm_rate': stats['false_alarm_rate'],
                    'accuracy': 1.0 - stats['false_alarm_rate'] if stats['total_feedback'] > 0 else 0.0
                },
                'threshold_adjustments': stats['threshold_adjustments'],
                'rules_tracked': stats['rules_tracked'],
                'problematic_rules': problematic_rules,
                'rule_performance': rule_performance,
                'recent_feedback': recent_feedback,
                'trend': {
                    'summary': trend_summary,
                    'daily': timeline,
                },
                'last_updated': stats['last_updated']
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting guardrail performance: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get guardrail performance',
            'message': str(e)
        }), 500

@app.route('/analytics/export-training-data', methods=['GET'])
def export_training_data():
    """Export feedback data in ML-ready format for model retraining"""
    try:
        if not feedback_learner:
            return jsonify({
                'success': False,
                'error': 'Feedback learner not available',
                'message': 'Adaptive learning is not enabled'
            }), 503
        
        format_type = request.args.get('format', 'json')  # json, csv, or parquet
        
        # Get all feedback data
        false_alarms = feedback_learner.false_alarms
        true_positives = feedback_learner.true_positives
        rule_stats = dict(feedback_learner.rule_statistics)
        
        # Prepare training data structure
        training_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'format': format_type,
                'total_false_alarms': len(false_alarms),
                'total_true_positives': len(true_positives),
                'rules_tracked': len(rule_stats)
            },
            'false_alarms': false_alarms,
            'true_positives': true_positives,
            'rule_statistics': rule_stats,
            'threshold_adjustments': feedback_learner.threshold_adjustments.copy()
        }
        
        if format_type == 'csv':
            # Convert to CSV format
            import csv
            import io
            output = io.StringIO()
            
            # Write false alarms
            if false_alarms:
                writer = csv.DictWriter(output, fieldnames=false_alarms[0].keys())
                writer.writeheader()
                writer.writerows(false_alarms)
            
            csv_data = output.getvalue()
            return jsonify({
                'success': True,
                'format': 'csv',
                'data': csv_data,
                'filename': f'guardrail_training_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }), 200
        else:
            # Default to JSON
            return jsonify({
                'success': True,
                'format': 'json',
                'data': training_data,
                'filename': f'guardrail_training_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }), 200
            
    except Exception as e:
        logger.error(f"Error exporting training data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to export training data',
            'message': str(e)
        }), 500

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
        conversation_history = data.get('conversation_history', None)  # Optional: list of previous messages
        
        logger.info(f"Validating message for conversation: {conversation_id}")
        
        # Validate message with optional conversation history for LLM context-aware check
        validation_results = validator.validate(
            message, 
            conversation_id, 
            user_id=user_id,
            conversation_history=conversation_history
        )
        
        # Failures are handled by kafka_handler.py automatically
        # We no longer send "passed" events to Kafka
        
        # Prepare response
        response = {
            'success': True,
            'valid': validation_results['valid'],
            'conversation_id': conversation_id,
            'validation_results': validation_results,
            'event': {
                'event_type': 'validation_passed' if validation_results['valid'] else 'validation_failed',
                'severity': 'info' if validation_results['valid'] else 'high',  # Generic failure severity
                'kafka_sent': not validation_results['valid']  # Only True if a failure was sent
            }
        }
        
        status_code = 200
        
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
    logger.info(f"Kafka producer: {'✅ Connected' if kafka_producer.producer else '⚠️ Disconnected'}")
    logger.info(f"Kafka consumer (guardrail_control): {'✅ Running' if (kafka_consumer and kafka_consumer.is_running()) else '⚠️ Stopped'}")
    logger.info(f"Kafka consumer (operator_actions): {'✅ Running' if (operator_actions_consumer and operator_actions_consumer.is_running()) else '⚠️ Stopped'}")
    logger.info(f"Validator settings - PII: {validator.enable_pii_detection}, "
                f"Toxicity: {validator.enable_toxicity_check}, "
                f"Compliance: {validator.enable_compliance_check}, "
                f"LLM Context Check: {validator.enable_llm_context_check}")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')
    except KeyboardInterrupt:
        logger.info("Shutting down guardrail service...")
        kafka_producer.close()
        if kafka_consumer:
            kafka_consumer.stop()
        if operator_actions_consumer:
            operator_actions_consumer.stop()
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        kafka_producer.close()
        if kafka_consumer:
            kafka_consumer.stop()
        if operator_actions_consumer:
            operator_actions_consumer.stop()
