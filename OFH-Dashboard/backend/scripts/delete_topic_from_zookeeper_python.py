#!/usr/bin/env python3
"""
Python script to delete a Kafka topic from ZooKeeper directly
This works even when Kafka is not running
"""

import sys
import os

try:
    from kazoo.client import KazooClient  # type: ignore
    from kazoo.exceptions import NoNodeError  # type: ignore
except ImportError:
    print("ERROR: kazoo library not installed")
    print("Install with: pip install kazoo")
    print()
    print("Alternatively, you can use zkCli if it's available in your Kafka installation.")
    sys.exit(1)

def delete_topic_from_zookeeper(topic_name, zookeeper_host="localhost:2181"):
    """Delete a topic from ZooKeeper metadata"""
    
    print("=" * 60)
    print(f"Deleting Topic from ZooKeeper: {topic_name}")
    print("=" * 60)
    print()
    print(f"Connecting to ZooKeeper at {zookeeper_host}...")
    
    zk = None
    try:
        # Connect to ZooKeeper
        zk = KazooClient(hosts=zookeeper_host)
        zk.start()
        print("✅ Connected to ZooKeeper")
        print()
        
        deleted_paths = []
        
        # Paths to delete
        paths_to_delete = [
            f"/brokers/topics/{topic_name}",
            f"/config/topics/{topic_name}",
            f"/admin/delete_topics/{topic_name}",
        ]
        
        # Try to delete each path
        for path in paths_to_delete:
            try:
                if zk.exists(path):
                    print(f"  Found: {path}")
                    # Delete recursively if it's a node with children
                    zk.delete(path, recursive=True)
                    print(f"  ✅ Deleted: {path}")
                    deleted_paths.append(path)
                else:
                    print(f"  ℹ️  Not found (already deleted): {path}")
            except NoNodeError:
                print(f"  ℹ️  Not found (already deleted): {path}")
            except Exception as e:
                print(f"  ⚠️  Error deleting {path}: {e}")
        
        # Also check for partition-specific paths
        try:
            topic_path = f"/brokers/topics/{topic_name}"
            if zk.exists(topic_path):
                # Get partitions
                partitions_path = f"{topic_path}/partitions"
                if zk.exists(partitions_path):
                    partitions = zk.get_children(partitions_path)
                    for partition in partitions:
                        partition_path = f"{partitions_path}/{partition}"
                        try:
                            zk.delete(partition_path, recursive=True)
                            print(f"  ✅ Deleted partition: {partition_path}")
                            deleted_paths.append(partition_path)
                        except Exception as e:
                            print(f"  ⚠️  Error deleting partition {partition_path}: {e}")
        except Exception as e:
            print(f"  ⚠️  Error checking partitions: {e}")
        
        print()
        if deleted_paths:
            print("=" * 60)
            print("✅ Topic metadata deleted from ZooKeeper")
            print("=" * 60)
            print()
            print("Deleted paths:")
            for path in deleted_paths:
                print(f"  - {path}")
            return True
        else:
            print("=" * 60)
            print("ℹ️  Topic not found in ZooKeeper (already deleted or never existed)")
            print("=" * 60)
            return True
            
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        print()
        print("Make sure ZooKeeper is running at", zookeeper_host)
        return False
    finally:
        if zk:
            zk.stop()
            zk.close()

if __name__ == "__main__":
    topic_name = "guardrail.control"
    zookeeper_host = os.getenv("ZOOKEEPER_HOST", "localhost:2181")
    
    success = delete_topic_from_zookeeper(topic_name, zookeeper_host)
    
    if success:
        print()
        print("Next steps:")
        print("1. Ensure Kafka is stopped")
        print("2. Delete the directory: C:\\tmp\\kafka-logs\\guardrail.control-0")
        print("3. Run: python scripts\\reset_kafka_log_dir_state.py")
        print("4. Start ZooKeeper")
        print("5. Start Kafka")
        sys.exit(0)
    else:
        sys.exit(1)

