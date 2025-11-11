#!/usr/bin/env python3
"""
Seed the feedback learner with sample data for UI testing.

Usage:
    python seed_feedback.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
for path in (PROJECT_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from services.learning.feedback_learner import FeedbackLearner


def main():
    learner = FeedbackLearner()

    for n in range(1, 7):
        learner.record_false_alarm(
            conversation_id=f"conv-pii-high-{n}",
            original_event_id=f"evt-pii-{n:03d}",
            feedback_content=f"PII alert {n} was a false alarm",
            triggered_rules=["DetectPII"],
            validator_type="pii",
        )

    learner.record_true_positive(
        conversation_id="conv-demo-2",
        event_id="evt-002",
        triggered_rules=["ToxicLanguage"],
        validator_type="toxicity",
    )

    learner.record_false_alarm(
        conversation_id="conv-compliance-1",
        original_event_id="evt-compliance-001",
        feedback_content="Compliance alert flagged the wrong phrase",
        triggered_rules=["medical_advice"],
        validator_type="compliance",
    )

    print("Seeded feedback:", learner.get_statistics())
    learner._save_feedback()  # Persist data for service reload


if __name__ == "__main__":
    main()

