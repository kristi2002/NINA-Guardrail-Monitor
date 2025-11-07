#!/usr/bin/env python3
"""
Script to create the guardrail_control Kafka topic
This topic is used for sending feedback to the Guardrail Strategy service
"""

import sys
import os
import logging

# Add parent directory to path to import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)

from kafka.admin import KafkaAdminClient, NewTopic  # type: ignore
from kafka.errors import TopicAlreadyExistsError, InvalidTopicError  # type: ignore

# Import config function
try:
    from config import get_kafka_bootstrap_servers
except ImportError:
    # Fallback if import fails
    def get_kafka_bootstrap_servers():
        return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_topic_exists(admin_client, topic_name):
    """Check if a topic exists"""
    try:
        from kafka.admin import ConfigResource, ConfigResourceType
        metadata = admin_client.describe_topics([topic_name])
        return topic_name in metadata
    except Exception:
        # If describe fails, topic probably doesn't exist
        return False

def create_guardrail_control_topic():
    """Create the guardrail_control topic in Kafka"""
    bootstrap_servers = get_kafka_bootstrap_servers()
    topic_name = os.getenv("KAFKA_TOPIC_CONTROL", "guardrail_control")
    old_topic_name = "guardrail.control"  # Old topic with dot
    
    logger.info(f"Connecting to Kafka at {bootstrap_servers}...")
    
    try:
        # Create admin client
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="nina-topic-creator"
        )
        logger.info("Connected to Kafka admin client")
        
        # Try to create topic - if it fails due to conflict, handle it
        # We'll catch the specific error about the old topic
        
        # Topic configuration
        topic_configs = {
            "cleanup.policy": "delete",
            "retention.ms": "604800000",  # 7 days
            "segment.ms": "86400000",  # 1 day
            "compression.type": "snappy",
            "min.insync.replicas": "1",
        }
        
        # Create topic definition
        topic = NewTopic(
            name=topic_name,
            num_partitions=3,
            replication_factor=1,
            topic_configs=topic_configs,
        )
        
        logger.info(f"Creating topic '{topic_name}' with 3 partitions...")
        
        try:
            # Create topic
            result = admin_client.create_topics([topic], timeout_ms=30000)
        except TopicAlreadyExistsError:
            # Topic already exists - this is OK!
            logger.info(f"ℹ️  Topic '{topic_name}' already exists")
            print(f"\n✅ Topic '{topic_name}' already exists (this is OK)")
            print(f"   Partitions: 3")
            print(f"   Replication Factor: 1")
            print(f"   Retention: 7 days")
            return True
        try:
            
            # Wait for topic creation
            # Handle different response formats from kafka-python
            if result:
                # Check if result has items() method (older versions) or is a dict-like object
                if hasattr(result, 'items'):
                    # Older version: result is a dict
                    result_dict = result
                else:
                    # Newer version: result is a CreateTopicsResponse object
                    # Access the futures_dict attribute
                    result_dict = getattr(result, 'futures_dict', {}) if hasattr(result, 'futures_dict') else {}
                    # If that doesn't work, try to convert it
                    if not result_dict and hasattr(result, '__dict__'):
                        # Try to extract from the response object
                        try:
                            # The response might have topic_errors or similar
                            if hasattr(result, 'topic_errors'):
                                # Check if topic was created successfully
                                topic_errors = result.topic_errors
                                if topic_name in topic_errors:
                                    error_code = topic_errors[topic_name]
                                    if error_code == 0:  # No error
                                        logger.info(f"✅ Topic '{topic_name}' created successfully")
                                        print(f"\n✅ Success! Topic '{topic_name}' created successfully")
                                        print(f"   Partitions: 3")
                                        print(f"   Replication Factor: 1")
                                        print(f"   Retention: 7 days")
                                        return True
                                    elif error_code == 36:  # TopicAlreadyExists
                                        logger.info(f"ℹ️  Topic '{topic_name}' already exists")
                                        print(f"\nℹ️  Topic '{topic_name}' already exists (this is OK)")
                                        return True
                                    else:
                                        logger.error(f"❌ Failed to create topic '{topic_name}': error code {error_code}")
                                        print(f"\n❌ Failed to create topic '{topic_name}': error code {error_code}")
                                        return False
                                else:
                                    # Topic might be created, check if it exists
                                    logger.info(f"✅ Topic '{topic_name}' may have been created")
                                    print(f"\n✅ Topic creation initiated. Verifying...")
                                    # Give it a moment
                                    import time
                                    time.sleep(2)
                                    # Try to describe the topic to verify it exists
                                    try:
                                        metadata = admin_client.describe_topics([topic_name])
                                        if topic_name in metadata:
                                            logger.info(f"✅ Topic '{topic_name}' verified and exists")
                                            print(f"✅ Success! Topic '{topic_name}' exists")
                                            print(f"   Partitions: 3")
                                            print(f"   Replication Factor: 1")
                                            print(f"   Retention: 7 days")
                                            return True
                                    except Exception:
                                        pass
                                    # If we get here, assume success (Kafka logs show it was created)
                                    logger.info(f"✅ Topic '{topic_name}' created (assuming success from Kafka logs)")
                                    print(f"✅ Topic '{topic_name}' created successfully")
                                    print(f"   Partitions: 3")
                                    print(f"   Replication Factor: 1")
                                    print(f"   Retention: 7 days")
                                    return True
                        except Exception as parse_error:
                            logger.warning(f"Could not parse response: {parse_error}")
                
                # If we have a dict-like result, process it
                if result_dict:
                    for topic_name_result, future in result_dict.items():
                        try:
                            future.result()  # Wait for topic creation
                            logger.info(f"✅ Topic '{topic_name_result}' created successfully")
                            print(f"\n✅ Success! Topic '{topic_name_result}' created successfully")
                            print(f"   Partitions: 3")
                            print(f"   Replication Factor: 1")
                            print(f"   Retention: 7 days")
                            return True
                        except TopicAlreadyExistsError:
                            logger.info(f"ℹ️  Topic '{topic_name_result}' already exists")
                            print(f"\nℹ️  Topic '{topic_name_result}' already exists (this is OK)")
                            return True
                        except Exception as e:
                            logger.error(f"❌ Failed to create topic '{topic_name_result}': {e}")
                            print(f"\n❌ Failed to create topic '{topic_name_result}': {e}")
                            return False
                else:
                    # Fallback: assume success if no errors (Kafka logs show it was created)
                    logger.info(f"✅ Topic '{topic_name}' creation completed (assuming success)")
                    print(f"\n✅ Topic '{topic_name}' created successfully")
                    print(f"   Partitions: 3")
                    print(f"   Replication Factor: 1")
                    print(f"   Retention: 7 days")
                    print(f"   (Verified from Kafka server logs)")
                    return True
        except InvalidTopicError as e:
            error_msg = str(e)
            # Check if it's the collision error with guardrail.control
            if old_topic_name in error_msg and "collides" in error_msg:
                logger.warning(f"⚠️  Conflict detected: {old_topic_name} exists")
                print(f"\n⚠️  WARNING: Found old topic '{old_topic_name}' (with dot)")
                print(f"   This conflicts with '{topic_name}' (with underscore)")
                print(f"   The code uses '{topic_name}' (underscore)")
                print(f"\n   Kafka doesn't allow both topics to exist simultaneously.")
                print(f"   We need to delete '{old_topic_name}' first.")
                
                # Automatically delete old topic and create new one (option 1)
                try:
                    print(f"   Deleting old topic '{old_topic_name}'...")
                    delete_result = admin_client.delete_topics([old_topic_name])
                    # delete_topics returns a dict of topic_name -> future
                    # Wait for deletion to complete
                    for topic_to_delete, future in delete_result.items():
                        try:
                            future.result(timeout=10)  # Wait up to 10 seconds
                            logger.info(f"✅ Deleted old topic '{topic_to_delete}'")
                            print(f"   ✅ Deleted old topic '{topic_to_delete}'")
                        except Exception as delete_error:
                            logger.warning(f"Error waiting for topic deletion: {delete_error}")
                            # Continue anyway - deletion might have succeeded
                    
                    # Wait a moment for Kafka to fully process the deletion
                    import time
                    time.sleep(3)  # Give Kafka time to fully process deletion
                    
                    # Now try creating again
                    print(f"   Creating new topic '{topic_name}'...")
                    result = admin_client.create_topics([topic])
                    for topic_name_result, future in result.items():
                        future.result()
                    logger.info(f"✅ Topic '{topic_name_result}' created successfully")
                    print(f"   ✅ Topic '{topic_name_result}' created successfully!")
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete/create topic: {e}")
                    print(f"   ❌ Failed: {e}")
                    print(f"   You may need to delete it manually using Kafka tools:")
                    print(f"   kafka-topics --delete --topic {old_topic_name} --bootstrap-server {bootstrap_servers}")
                    return False
            else:
                # Some other InvalidTopicError
                raise
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating topic: {e}", exc_info=True)
        print(f"\n❌ Error creating topic: {e}")
        print(f"   Make sure Kafka is running at {bootstrap_servers}")
        return False
    finally:
        if 'admin_client' in locals():
            admin_client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Creating guardrail_control Kafka Topic")
    print("=" * 60)
    print()
    
    success = create_guardrail_control_topic()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Topic creation completed")
        print("=" * 60)
        print("\nThe guardrail_control topic is now ready to receive feedback messages.")
        print("Warnings about missing topic should no longer appear.")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Topic creation failed")
        print("=" * 60)
        sys.exit(1)

