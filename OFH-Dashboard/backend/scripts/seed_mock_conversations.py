#!/usr/bin/env python3
"""
Seed Mock Conversations with Diverse Cases

This script creates 15 diverse conversation sessions with different:
- Risk levels (LOW, MEDIUM, HIGH, CRITICAL)
- Statuses (ACTIVE, COMPLETED, TERMINATED, ESCALATED)
- Situations (medical questions, emergencies, routine checkups, etc.)
- Guardrail violations (some with, some without)
- Patient demographics and pathologies

Usage:
    # From project root
    cd OFH-Dashboard/backend
    python scripts/seed_mock_conversations.py
    
    # Or from Docker
    docker compose exec ofh-dashboard-backend python scripts/seed_mock_conversations.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

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


def tz_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def generate_conversation_id() -> str:
    """Generate a unique conversation ID"""
    return f"{CONV_PREFIX}{uuid.uuid4().hex[:12]}"


def generate_event_id() -> str:
    """Generate a unique event ID"""
    return f"{EVENT_PREFIX}{uuid.uuid4().hex[:12]}"


def generate_message_id() -> str:
    """Generate a unique message ID"""
    return f"msg_{uuid.uuid4().hex[:12]}"


# Define 15 diverse conversation scenarios
CONVERSATION_SCENARIOS = [
    {
        "patient_id": "PAT001",
        "patient_name": "Mario Rossi",
        "age": 45,
        "gender": "M",
        "pathology": "Ipertensione",
        "situation": "Controllo pressione arteriosa",
        "risk_level": "LOW",
        "status": "COMPLETED",
        "guardrail_violations": 0,
        "total_messages": 8,
        "sentiment_score": 0.6,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Buongiorno, vorrei sapere come misurare correttamente la pressione arteriosa."},
            {"sender": "bot", "content": "Buongiorno! Per misurare correttamente la pressione arteriosa, è importante essere a riposo da almeno 5 minuti..."},
            {"sender": "user", "content": "Grazie, e quando devo preoccuparmi?"},
            {"sender": "bot", "content": "Valori superiori a 140/90 mmHg richiedono attenzione medica. Consiglio di consultare il medico."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT002",
        "patient_name": "Laura Bianchi",
        "age": 32,
        "gender": "F",
        "pathology": "Diabete tipo 2",
        "situation": "Gestione glicemia",
        "risk_level": "MEDIUM",
        "status": "ACTIVE",
        "guardrail_violations": 1,
        "total_messages": 12,
        "sentiment_score": 0.3,
        "requires_attention": True,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ho misurato la glicemia e ho 250 mg/dL, è normale?"},
            {"sender": "bot", "content": "Un valore di 250 mg/dL è elevato. Consiglio di contattare immediatamente il medico..."},
            {"sender": "user", "content": "Ma posso prendere più insulina da sola?"},
            {"sender": "bot", "content": "⚠️ Non posso fornire consigli specifici su dosaggi di farmaci. Consulti il medico."},
        ],
        "events": [
            {"type": "medication_warning", "severity": "HIGH", "message": "Richiesta di consiglio su dosaggio farmaco senza supervisione medica"},
        ],
    },
    {
        "patient_id": "PAT003",
        "patient_name": "Giuseppe Verdi",
        "age": 67,
        "gender": "M",
        "pathology": "Cardiopatia ischemica",
        "situation": "Dolore toracico acuto",
        "risk_level": "CRITICAL",
        "status": "ESCALATED",
        "guardrail_violations": 2,
        "total_messages": 6,
        "sentiment_score": -0.4,
        "requires_attention": True,
        "escalated": True,
        "messages": [
            {"sender": "user", "content": "Ho un forte dolore al petto da 10 minuti, cosa devo fare?"},
            {"sender": "bot", "content": "⚠️ EMERGENZA: Dolore toracico richiede assistenza immediata. Chiami il 118 subito!"},
            {"sender": "user", "content": "Ma potrebbe essere solo bruciore di stomaco?"},
            {"sender": "bot", "content": "Non posso escludere cause cardiache. Chiami il 118 immediatamente."},
        ],
        "events": [
            {"type": "emergency_protocol", "severity": "CRITICAL", "message": "Dolore toracico acuto - richiesta assistenza urgente"},
            {"type": "alarm_triggered", "severity": "HIGH", "message": "Possibile emergenza cardiaca rilevata"},
        ],
    },
    {
        "patient_id": "PAT004",
        "patient_name": "Anna Neri",
        "age": 28,
        "gender": "F",
        "pathology": "Gravidanza",
        "situation": "Domande su gravidanza",
        "risk_level": "LOW",
        "status": "COMPLETED",
        "guardrail_violations": 0,
        "total_messages": 10,
        "sentiment_score": 0.7,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Sono incinta di 3 mesi, posso fare attività fisica?"},
            {"sender": "bot", "content": "Sì, l'attività fisica moderata è generalmente consigliata in gravidanza..."},
            {"sender": "user", "content": "E quali sport sono sicuri?"},
            {"sender": "bot", "content": "Camminata, nuoto e yoga prenatale sono generalmente sicuri. Eviti sport di contatto."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT005",
        "patient_name": "Marco Blu",
        "age": 19,
        "gender": "M",
        "pathology": "Nessuna patologia nota",
        "situation": "Richiesta informazioni inappropriate",
        "risk_level": "MEDIUM",
        "status": "TERMINATED",
        "guardrail_violations": 1,
        "total_messages": 4,
        "sentiment_score": 0.1,
        "requires_attention": True,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ciao, come posso ottenere farmaci senza ricetta?"},
            {"sender": "bot", "content": "Non posso fornire informazioni su come ottenere farmaci senza prescrizione medica."},
            {"sender": "user", "content": "Ma è per un amico, non per me"},
            {"sender": "bot", "content": "⚠️ Richiesta inappropriata rilevata. La conversazione è stata terminata."},
        ],
        "events": [
            {"type": "inappropriate_content", "severity": "MEDIUM", "message": "Tentativo di ottenere farmaci senza prescrizione"},
        ],
    },
    {
        "patient_id": "PAT006",
        "patient_name": "Sofia Gialli",
        "age": 55,
        "gender": "F",
        "pathology": "Artrite reumatoide",
        "situation": "Gestione dolore cronico",
        "risk_level": "MEDIUM",
        "status": "ACTIVE",
        "guardrail_violations": 0,
        "total_messages": 15,
        "sentiment_score": 0.2,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Il dolore alle articolazioni è peggiorato ultimamente"},
            {"sender": "bot", "content": "Capisco. Ha notato se ci sono fattori scatenanti? Attività specifiche, cambiamenti meteo?"},
            {"sender": "user", "content": "Sì, quando piove fa più male"},
            {"sender": "bot", "content": "È comune. Consiglio di consultare il reumatologo per valutare eventuali modifiche terapeutiche."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT007",
        "patient_name": "Luca Rossi",
        "age": 8,
        "gender": "M",
        "pathology": "Asma",
        "situation": "Crisi asmatica",
        "risk_level": "HIGH",
        "status": "ESCALATED",
        "guardrail_violations": 1,
        "total_messages": 5,
        "sentiment_score": -0.5,
        "requires_attention": True,
        "escalated": True,
        "messages": [
            {"sender": "user", "content": "Mio figlio ha difficoltà a respirare, cosa faccio?"},
            {"sender": "bot", "content": "⚠️ Se ha difficoltà respiratorie, somministri immediatamente il broncodilatatore e chiami il 118 se non migliora."},
            {"sender": "user", "content": "Ho già dato il farmaco ma respira ancora male"},
            {"sender": "bot", "content": "Chiami immediatamente il 118. Crisi asmatica grave richiede assistenza urgente."},
        ],
        "events": [
            {"type": "emergency_protocol", "severity": "HIGH", "message": "Crisi asmatica pediatrica - richiesta assistenza urgente"},
        ],
    },
    {
        "patient_id": "PAT008",
        "patient_name": "Elena Verde",
        "age": 42,
        "gender": "F",
        "pathology": "Depressione",
        "situation": "Supporto psicologico",
        "risk_level": "HIGH",
        "status": "ACTIVE",
        "guardrail_violations": 2,
        "total_messages": 20,
        "sentiment_score": -0.6,
        "requires_attention": True,
        "escalated": True,
        "messages": [
            {"sender": "user", "content": "Non riesco più a vedere una via d'uscita"},
            {"sender": "bot", "content": "Capisco che stia attraversando un momento difficile. È importante parlarne con un professionista..."},
            {"sender": "user", "content": "A volte penso che sarebbe meglio se non ci fossi"},
            {"sender": "bot", "content": "⚠️ Se ha pensieri di autolesionismo, contatti immediatamente il Telefono Amico 199 284 284 o il 118."},
        ],
        "events": [
            {"type": "self_harm", "severity": "CRITICAL", "message": "Indicazioni di pensieri autolesionistici rilevate"},
            {"type": "alarm_triggered", "severity": "HIGH", "message": "Richiesta assistenza psicologica urgente"},
        ],
    },
    {
        "patient_id": "PAT009",
        "patient_name": "Roberto Marrone",
        "age": 60,
        "gender": "M",
        "pathology": "BPCO",
        "situation": "Routine checkup",
        "risk_level": "LOW",
        "status": "COMPLETED",
        "guardrail_violations": 0,
        "total_messages": 7,
        "sentiment_score": 0.5,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Quando devo fare il prossimo controllo?"},
            {"sender": "bot", "content": "Per la BPCO, consiglio controlli ogni 6 mesi o secondo indicazione del pneumologo."},
            {"sender": "user", "content": "Grazie, e per la terapia?"},
            {"sender": "bot", "content": "Continui la terapia prescritta. Se nota peggioramenti, contatti il medico prima del controllo."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT010",
        "patient_name": "Francesca Viola",
        "age": 35,
        "gender": "F",
        "pathology": "Tiroidite di Hashimoto",
        "situation": "Domande su farmaci",
        "risk_level": "MEDIUM",
        "status": "COMPLETED",
        "guardrail_violations": 1,
        "total_messages": 9,
        "sentiment_score": 0.4,
        "requires_attention": True,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ho dimenticato di prendere la levotiroxina ieri, devo raddoppiare oggi?"},
            {"sender": "bot", "content": "No, non raddoppi la dose. Prenda la dose normale oggi e continui normalmente."},
            {"sender": "user", "content": "E se dimentico spesso?"},
            {"sender": "bot", "content": "⚠️ L'aderenza terapeutica è importante. Parli con il medico se ha difficoltà a ricordare."},
        ],
        "events": [
            {"type": "medication_warning", "severity": "MEDIUM", "message": "Richiesta di modifica autonomica della terapia"},
        ],
    },
    {
        "patient_id": "PAT011",
        "patient_name": "Alessandro Arancione",
        "age": 25,
        "gender": "M",
        "pathology": "Nessuna patologia nota",
        "situation": "Informazioni generali",
        "risk_level": "LOW",
        "status": "COMPLETED",
        "guardrail_violations": 0,
        "total_messages": 6,
        "sentiment_score": 0.6,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Quali sono i sintomi dell'influenza?"},
            {"sender": "bot", "content": "I sintomi comuni includono febbre, mal di testa, dolori muscolari, tosse..."},
            {"sender": "user", "content": "Grazie per le informazioni"},
            {"sender": "bot", "content": "Prego! Se i sintomi persistono o peggiorano, consulti il medico."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT012",
        "patient_name": "Valentina Rosa",
        "age": 50,
        "gender": "F",
        "pathology": "Osteoporosi",
        "situation": "Prevenzione cadute",
        "risk_level": "MEDIUM",
        "status": "ACTIVE",
        "guardrail_violations": 0,
        "total_messages": 11,
        "sentiment_score": 0.3,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ho paura di cadere, cosa posso fare per prevenirlo?"},
            {"sender": "bot", "content": "Per prevenire le cadute, consiglio esercizi di equilibrio, rimozione di ostacoli in casa..."},
            {"sender": "user", "content": "E per l'alimentazione?"},
            {"sender": "bot", "content": "Calcio e vitamina D sono importanti. Consiglio di consultare un nutrizionista."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT013",
        "patient_name": "Davide Celeste",
        "age": 38,
        "gender": "M",
        "pathology": "Ansia generalizzata",
        "situation": "Gestione ansia",
        "risk_level": "MEDIUM",
        "status": "COMPLETED",
        "guardrail_violations": 0,
        "total_messages": 14,
        "sentiment_score": 0.1,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ho attacchi di ansia frequenti, cosa posso fare?"},
            {"sender": "bot", "content": "Per gestire l'ansia, tecniche di respirazione e mindfulness possono aiutare..."},
            {"sender": "user", "content": "E se non funziona?"},
            {"sender": "bot", "content": "Se l'ansia interferisce con la vita quotidiana, consiglio di consultare uno psicologo o psichiatra."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT014",
        "patient_name": "Chiara Indaco",
        "age": 29,
        "gender": "F",
        "pathology": "Emicrania",
        "situation": "Gestione attacco emicrania",
        "risk_level": "MEDIUM",
        "status": "COMPLETED",
        "guardrail_violations": 1,
        "total_messages": 8,
        "sentiment_score": -0.2,
        "requires_attention": True,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ho un forte mal di testa da 3 giorni, cosa prendo?"},
            {"sender": "bot", "content": "Per l'emicrania, può provare farmaci antinfiammatori. Se persiste, consulti il medico."},
            {"sender": "user", "content": "Posso prendere più farmaci insieme per farlo passare prima?"},
            {"sender": "bot", "content": "⚠️ Non mescoli farmaci senza consultare il medico. Rischio di interazioni pericolose."},
        ],
        "events": [
            {"type": "medication_warning", "severity": "MEDIUM", "message": "Richiesta di combinazione non supervisionata di farmaci"},
        ],
    },
    {
        "patient_id": "PAT015",
        "patient_name": "Stefano Turchese",
        "age": 71,
        "gender": "M",
        "pathology": "Demenza lieve",
        "situation": "Supporto caregiver",
        "risk_level": "LOW",
        "status": "COMPLETED",
        "guardrail_violations": 0,
        "total_messages": 12,
        "sentiment_score": 0.4,
        "requires_attention": False,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Mio padre ha la demenza, come posso aiutarlo?"},
            {"sender": "bot", "content": "Per supportare una persona con demenza, è importante mantenere routine, comunicazione chiara..."},
            {"sender": "user", "content": "E se si agita?"},
            {"sender": "bot", "content": "In caso di agitazione, mantenga la calma, rassicuri e distragga. Se necessario, consulti il medico."},
        ],
        "events": [],
    },
    {
        "patient_id": "PAT016",
        "patient_name": "Giulia Argento",
        "age": 35,
        "gender": "F",
        "pathology": "Richiesta informazioni",
        "situation": "Violazione Dati Personali (PII)",
        "risk_level": "MEDIUM",
        "status": "ACTIVE",
        "guardrail_violations": 1,
        "total_messages": 4,
        "sentiment_score": 0.3,
        "requires_attention": True,
        "escalated": False,
        "messages": [
            {"sender": "user", "content": "Ecco i miei dati per la pratica: mi chiamo Giulia Argento e il mio codice fiscale è RGLGLA85M45H501X. La mia mail è giulia.argento@email.it e il mio numero di telefono è 3331234567."},
            {"sender": "bot", "content": "⚠️ Ho rilevato dati personali sensibili nel suo messaggio. Per proteggere la sua privacy e rispettare il GDPR, non posso elaborare informazioni come codice fiscale, email o numeri di telefono. La prego di contattare direttamente il servizio clienti per questo tipo di richieste."},
            {"sender": "user", "content": "Ma ho bisogno di inviare questi dati per la pratica medica."},
            {"sender": "bot", "content": "Comprendo la sua necessità. Per questioni di sicurezza e privacy, i dati sensibili devono essere inviati tramite canali sicuri e autorizzati. La prego di utilizzare il portale paziente ufficiale o contattare la segreteria."},
        ],
        "events": [
            {
                "type": "privacy_violation_prevented",
                "severity": "MEDIUM",
                "message": "Rilevamento Dati Personali (PII): Codice Fiscale italiano, indirizzo email e numero di telefono rilevati nel messaggio utente",
                "details": {
                    "pii_types": ["IT_FISCAL_CODE", "EMAIL_ADDRESS", "PHONE_NUMBER"],
                    "entities_detected": [
                        {"type": "IT_FISCAL_CODE", "value": "RGLGLA85M45H501X", "confidence": 0.98},
                        {"type": "EMAIL_ADDRESS", "value": "giulia.argento@email.it", "confidence": 0.99},
                        {"type": "PHONE_NUMBER", "value": "3331234567", "confidence": 0.95}
                    ],
                    "gdpr_compliance": "violation_prevented"
                }
            },
        ],
    },
]


def create_conversation(session, scenario: Dict[str, Any], base_time: datetime) -> ConversationSession:
    """Create a conversation session from a scenario"""
    conv_id = generate_conversation_id()
    
    # Calculate session timing
    hours_ago = len(CONVERSATION_SCENARIOS) - CONVERSATION_SCENARIOS.index(scenario)
    session_start = base_time - timedelta(hours=hours_ago)
    
    # Determine session end based on status
    if scenario["status"] == "ACTIVE":
        session_end = None
        duration = None
    else:
        duration_minutes = scenario.get("total_messages", 8) * 2  # ~2 min per message
        session_end = session_start + timedelta(minutes=duration_minutes)
        duration = duration_minutes
    
    # Create patient info
    patient_info = {
        "name": scenario["patient_name"],
        "age": scenario["age"],
        "gender": scenario["gender"],
        "pathology": scenario["pathology"],
    }
    
    # Create conversation
    conversation = ConversationSession(
        id=conv_id,
        patient_id=scenario["patient_id"],
        patient_info=patient_info,
        session_start=session_start,
        session_end=session_end,
        session_duration_minutes=duration,
        status=scenario["status"],
        total_messages=scenario["total_messages"],
        guardrail_violations=scenario["guardrail_violations"],
        risk_level=scenario["risk_level"],
        situation=scenario["situation"],
        is_monitored=True,
        requires_attention=scenario["requires_attention"],
        escalated=scenario["escalated"],
        sentiment_score=scenario["sentiment_score"],
        engagement_score=0.5 + (scenario["sentiment_score"] * 0.3),
        satisfaction_score=0.6 + (scenario["sentiment_score"] * 0.2),
    )
    
    session.add(conversation)
    session.flush()  # Get the ID
    
    # Create messages
    message_time = session_start
    for idx, msg_data in enumerate(scenario["messages"], 1):
        message = ChatMessage(
            message_id=generate_message_id(),
            conversation_id=conv_id,
            content=msg_data["content"],
            message_type="text",
            sender_type=msg_data["sender"],
            sender_id=scenario["patient_id"] if msg_data["sender"] == "user" else "nina_bot",
            sender_name=scenario["patient_name"] if msg_data["sender"] == "user" else "NINA Assistant",
            timestamp=message_time,
            sequence_number=idx,
            sentiment_score=scenario["sentiment_score"] if msg_data["sender"] == "user" else 0.5,
            language="it",
            risk_score=0.3 if scenario["risk_level"] in ["HIGH", "CRITICAL"] else 0.1,
            contains_sensitive_content=scenario["guardrail_violations"] > 0,
        )
        session.add(message)
        message_time += timedelta(minutes=2)
    
    # Create guardrail events
    for event_data in scenario["events"]:
        event_time = session_start + timedelta(minutes=5)
        
        # Get the user message that triggered the event (usually the first one with sensitive content)
        user_message = next((msg["content"] for msg in scenario["messages"] if msg["sender"] == "user"), "")
        bot_response = next((msg["content"] for msg in scenario["messages"] if msg["sender"] == "bot" and "⚠️" in msg["content"]), "")
        
        # Build event details
        event_details = event_data.get("details", {})
        if not event_details and event_data["type"] == "privacy_violation_prevented":
            # Extract PII from user message if details not provided
            event_details = {
                "pii_types": [],
                "entities_detected": [],
                "gdpr_compliance": "violation_prevented"
            }
        
        # Determine detected text for PII events
        if event_data["type"] == "privacy_violation_prevented" and event_details.get("entities_detected"):
            detected_text = ", ".join([e.get("value", "") for e in event_details["entities_detected"]])
        else:
            detected_text = user_message[:200] if user_message else ""
        
        # Determine tags
        tags = "PII,GDPR"
        if event_details.get("pii_types"):
            tags += "," + ",".join(event_details["pii_types"])
        
        event = GuardrailEvent(
            event_id=generate_event_id(),
            conversation_id=conv_id,
            event_type=event_data["type"],
            severity=event_data["severity"],
            category="alert",
            title="Rilevamento Dati Personali (PII)" if event_data["type"] == "privacy_violation_prevented" else f"Evento: {event_data['type']}",
            description=event_data["message"],
            message_content=user_message,
            detected_text=detected_text,
            confidence_score=0.95 if event_data["type"] == "privacy_violation_prevented" else (0.85 if event_data["severity"] in ["HIGH", "CRITICAL"] else 0.7),
            detection_method="ai_model",
            model_version="v2.0",
            status="PENDING",
            priority="HIGH" if event_data["type"] == "privacy_violation_prevented" else ("URGENT" if event_data["severity"] == "CRITICAL" else "HIGH"),
            tags=tags,
            user_message=user_message,
            bot_response=bot_response,
            created_at=event_time,
            details=event_details if event_details else None,
        )
        session.add(event)
    
    return conversation


def main():
    """Main function to seed mock conversations"""
    print("=" * 60)
    print("NINA Guardrail Monitor - Seed Mock Conversations")
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
        
        # Create conversations
        base_time = tz_now()
        created_count = 0
        
        with get_session_context() as session:
            print(f"Creating {len(CONVERSATION_SCENARIOS)} diverse conversations...")
            print()
            
            for idx, scenario in enumerate(CONVERSATION_SCENARIOS, 1):
                try:
                    conversation = create_conversation(session, scenario, base_time)
                    created_count += 1
                    print(f"  [{idx}/{len(CONVERSATION_SCENARIOS)}] ✅ Created: {scenario['patient_name']} - {scenario['situation']} ({scenario['risk_level']} risk)")
                except Exception as e:
                    print(f"  [{idx}/{len(CONVERSATION_SCENARIOS)}] ❌ Failed: {scenario['patient_name']} - {e}")
            
            session.commit()
        
        print()
        print("=" * 60)
        print(f"✅ Successfully created {created_count} conversations with diverse cases!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  • Total conversations: {created_count}")
        print(f"  • With guardrail violations: {sum(1 for s in CONVERSATION_SCENARIOS if s['guardrail_violations'] > 0)}")
        print(f"  • Escalated: {sum(1 for s in CONVERSATION_SCENARIOS if s['escalated'])}")
        print(f"  • Risk levels:")
        for risk in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            count = sum(1 for s in CONVERSATION_SCENARIOS if s['risk_level'] == risk)
            print(f"    - {risk}: {count}")
        print()
        print("You can now view these conversations in the dashboard!")
        
    except Exception as e:
        print(f"❌ Error seeding conversations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

