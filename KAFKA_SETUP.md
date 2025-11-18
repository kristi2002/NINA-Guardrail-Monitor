# Kafka Setup Guide (WSL 2)

This guide explains how to set up and run Kafka in WSL 2 (Ubuntu) for the NINA Guardrail Monitor system.

## ⚠️ Important: WSL 2 IP Address Changes

**WSL 2 changes its IP address every time you restart your computer.**

- Today your IP might be: `192.168.216.165`
- Tomorrow it might be: `172.x.x.x` or another address

**You must update your configuration files whenever the IP changes.**

## 📋 First-Time Setup

### 1. Get Your WSL 2 IP Address

Open Ubuntu terminal and run:

```bash
hostname -I
```

This will show your current WSL 2 IP address (e.g., `192.168.216.165`).

### 2. Update Configuration Files

You need to update the IP address in two places:

#### A. Update `.env` Files

**Guardrail-Strategy** (`Guardrail-Strategy/.env`):
```env
KAFKA_BOOTSTRAP_SERVERS=192.168.216.165:9092
```

**OFH Dashboard Backend** (`OFH-Dashboard/backend/.env`):
```env
KAFKA_BOOTSTRAP_SERVERS=192.168.216.165:9092
```

Replace `192.168.216.165` with your actual WSL 2 IP address.

#### B. Update Kafka `server.properties`

In Ubuntu, edit the Kafka server configuration:

```bash
cd kafka_2.13-3.6.1
nano config/server.properties
```

Find and update the `listeners` and `advertised.listeners` settings:

```properties
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://192.168.216.165:9092
```

Replace `192.168.216.165` with your actual WSL 2 IP address.

## 🚀 Daily Startup Routine

Follow these steps every time you start working:

### Step 1: Check Your IP Address

Open Ubuntu terminal:

```bash
hostname -I
```

**If the IP has changed**, update:
- `.env` files in both `Guardrail-Strategy` and `OFH-Dashboard/backend`
- `config/server.properties` in Kafka installation

### Step 2: Start Zookeeper

In Ubuntu terminal:

```bash
cd kafka_2.13-3.6.1
bin/zookeeper-server-start.sh config/zookeeper.properties
```

Keep this terminal open. Zookeeper must be running before Kafka.

### Step 3: Start Kafka

Open a **new** Ubuntu terminal:

```bash
cd kafka_2.13-3.6.1
bin/kafka-server-start.sh config/server.properties
```

Keep this terminal open. Kafka must be running for the services to connect.

### Step 4: Start Python Services

In PowerShell (Windows):

```bash
# Start Guardrail-Strategy
cd Guardrail-Strategy
python app.py

# Or start OFH Dashboard Backend
cd OFH-Dashboard\backend
python app.py
```

## 🔍 Verifying Kafka is Running

### Check if Kafka is accessible from Windows

In PowerShell:

```powershell
Test-NetConnection -ComputerName 192.168.216.165 -Port 9092
```

Replace `192.168.216.165` with your current WSL 2 IP.

### Check Kafka topics

In Ubuntu terminal:

```bash
cd kafka_2.13-3.6.1
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

You should see topics like:
- `guardrail_events`
- `operator_actions`
- `guardrail_control` (optional)
- `dead_letter_queue`

## 🛠️ Troubleshooting

### Problem: Can't connect to Kafka from Windows

**Solution**: 
1. Check your WSL 2 IP: `hostname -I` in Ubuntu
2. Verify the IP in `.env` files matches
3. Verify `server.properties` has the correct IP in `advertised.listeners`
4. Restart Kafka after updating configuration

### Problem: IP changed after restart

**Solution**:
1. Get new IP: `hostname -I`
2. Update `.env` files
3. Update `config/server.properties`
4. Restart Zookeeper and Kafka

### Problem: Kafka won't start

**Solution**:
1. Make sure Zookeeper is running first
2. Check if port 9092 is already in use
3. Check Kafka logs in `kafka_2.13-3.6.1/logs/`

### Problem: "NoBrokersAvailable" error

**Solution**:
1. Verify Kafka is running in Ubuntu
2. Check IP address matches in all config files
3. Verify `advertised.listeners` in `server.properties` is correct
4. Try restarting Kafka

## 📝 Quick Reference

### Get WSL 2 IP
```bash
hostname -I
```

### Start Zookeeper
```bash
cd kafka_2.13-3.6.1
bin/zookeeper-server-start.sh config/zookeeper.properties
```

### Start Kafka
```bash
cd kafka_2.13-3.6.1
bin/kafka-server-start.sh config/server.properties
```

### List Topics
```bash
cd kafka_2.13-3.6.1
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Stop Kafka
Press `Ctrl+C` in the Kafka terminal

### Stop Zookeeper
Press `Ctrl+C` in the Zookeeper terminal

## 🔄 Workflow Summary

**Every Morning (or after restart):**

1. ✅ Open Ubuntu → `hostname -I` → Note the IP
2. ✅ If IP changed → Update `.env` files and `server.properties`
3. ✅ Start Zookeeper (Terminal 1)
4. ✅ Start Kafka (Terminal 2)
5. ✅ Start Python services (PowerShell)

**That's it!** Kafka should now be accessible from your Windows services.

