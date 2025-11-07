#!/usr/bin/env python3
"""
Python script to delete the guardrail.control topic from Kafka
This should be run while Kafka is running
"""

import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)

try:
    from kafka.admin import KafkaAdminClient, ConfigResource, ConfigResourceType  # type: ignore
    from kafka.errors import UnknownTopicOrPartitionError  # type: ignore
except ImportError:
    print("ERROR: kafka-python not installed")
    print("Install with: pip install kafka-python")
    sys.exit(1)

try:
    from config import get_kafka_bootstrap_servers
except ImportError:
    def get_kafka_bootstrap_servers():
        return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

def delete_topic(topic_name):
    """Delete a topic from Kafka"""
    bootstrap_servers = get_kafka_bootstrap_servers()
    
    print("=" * 60)
    print(f"Deleting Topic: {topic_name}")
    print("=" * 60)
    print()
    print(f"Connecting to Kafka at {bootstrap_servers}...")
    
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="nina-topic-deleter"
        )
        print("Connected to Kafka admin client")
        
        # Delete the topic
        print(f"Deleting topic '{topic_name}'...")
        try:
            result = admin_client.delete_topics([topic_name])
            
            # Wait for deletion
            for topic, future in result.items():
                try:
                    future.result(timeout=30)
                    print(f"✅ Topic '{topic_name}' deleted successfully")
                    return True
                except UnknownTopicOrPartitionError:
                    print(f"ℹ️  Topic '{topic_name}' does not exist (already deleted)")
                    return True
                except Exception as e:
                    print(f"❌ Failed to delete topic '{topic_name}': {e}")
                    return False
        except UnknownTopicOrPartitionError:
            print(f"ℹ️  Topic '{topic_name}' does not exist")
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Make sure Kafka is running at {bootstrap_servers}")
        return False
    finally:
        if 'admin_client' in locals():
            admin_client.close()

if __name__ == "__main__":
    topic_name = "guardrail.control"
    success = delete_topic(topic_name)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Topic deletion completed")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Stop Kafka")
        print("2. Manually delete: C:\\tmp\\kafka-logs\\guardrail.control-0")
        print("3. Run: python scripts\\reset_kafka_log_dir_state.py")
        print("4. Start Kafka")
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ Topic deletion failed")
        print("=" * 60)
        sys.exit(1)

