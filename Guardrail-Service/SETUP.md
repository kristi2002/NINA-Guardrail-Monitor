# Guardrail Service Setup Guide

## Step 1: Create Virtual Environment

```powershell
# Navigate to Guardrail-Service
cd Guardrail-Service

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Linux/Mac)
source venv/bin/activate
```

## Step 2: Install Dependencies

```bash
pip install guardrails-ai
pip install flask
pip install kafka-python
pip install openai
pip install python-dotenv
pip install requests
pip install jsonschema
```

Or install all at once:
```bash
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
# Copy the example environment file
copy env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY=your-key-here
# - GUARDRAILS_API_KEY=your-key-here (if using Guardrails Cloud)
# - KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## Step 4: Run the Service

```bash
python app.py
```

The service will start on **http://localhost:5001**

## Verify It's Working

```bash
# Test health endpoint
curl http://localhost:5001/health

# Or in browser: http://localhost:5001/health
```

## Project Structure

```
Guardrail-Service/
├── app.py              # Flask app (port 5001)
├── validators.py       # Guardrail validation logic
├── requirements.txt    # Dependencies
├── env.example         # Environment template
├── .env               # Your config (create this)
├── README.md          # Documentation
└── SETUP.md           # This file
```

## Integration with OFH-Dashboard

- **OFH-Dashboard** (port 5000) - System 1: Monitoring
- **Guardrail-Service** (port 5001) - System 2: The Guard

Both services communicate via Kafka topics.

