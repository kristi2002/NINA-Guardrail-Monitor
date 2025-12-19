#!/usr/bin/env python3
"""
Clear Mock Data Script

This script deletes all mock conversations and related data (messages, guardrail events)
that were created by the seed_mock_conversations.py script.

Usage:
    # From project root
    cd OFH-Dashboard/backend
    python scripts/clear_mock_data.py
    
    # Or from Docker
    docker compose exec ofh-dashboard-backend python scripts/clear_mock_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend package is importable when executed directly
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

from core.database import get_database_manager, get_session_context
from models import ConversationSession, ChatMessage, GuardrailEvent

CONV_PREFIX = "mock_conv_"
EVENT_PREFIX = "mock_event_"


def main():
    """Main function to clear mock data"""
    print("=" * 60)
    print("NINA Guardrail Monitor - Clear Mock Data")
    print("=" * 60)
    print()
    
    try:
        # Get database manager
        db_manager = get_database_manager()
        
        # Test connection
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            sys.exit(1)
        
        print("✅ Database connection successful")
        print()
        
        with get_session_context() as session:
            # Find all mock conversations
            mock_conversations = session.query(ConversationSession).filter(
                ConversationSession.id.like(f"{CONV_PREFIX}%")
            ).all()
            
            print(f"Found {len(mock_conversations)} mock conversations to delete")
            
            if len(mock_conversations) == 0:
                print("✅ No mock data found. Database is already clean.")
                return
            
            deleted_messages = 0
            deleted_events = 0
            deleted_conversations = 0
            
            for conversation in mock_conversations:
                # Delete related chat messages
                messages = session.query(ChatMessage).filter(
                    ChatMessage.conversation_id == conversation.id
                ).all()
                for message in messages:
                    session.delete(message)
                    deleted_messages += 1
                
                # Delete related guardrail events
                events = session.query(GuardrailEvent).filter(
                    GuardrailEvent.conversation_id == conversation.id
                ).all()
                for event in events:
                    session.delete(event)
                    deleted_events += 1
                
                # Delete the conversation
                session.delete(conversation)
                deleted_conversations += 1
            
            session.commit()
            
            print()
            print("=" * 60)
            print(f"✅ Successfully deleted mock data!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  • Deleted conversations: {deleted_conversations}")
            print(f"  • Deleted messages: {deleted_messages}")
            print(f"  • Deleted guardrail events: {deleted_events}")
            print()
        
    except Exception as e:
        print(f"❌ Error clearing mock data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

