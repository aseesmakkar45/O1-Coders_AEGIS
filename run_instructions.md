# AEGIS System Run Instructions

AEGIS is designed to be completely frictionless. The backend serves the React dashboard directly as a monolithic block, meaning there is zero `npm install` and zero separated frontend server to manage.

---

## 1. Prerequisites

You need two things to run this system:
* **Python 3.10** (A virtual environment using Conda or standard `venv` is highly recommended)
* A modern web browser (Chrome, Edge, or Firefox)

## 2. Environment Setup

From the project root directory, initialize your isolated environment:

```bash
conda create -n AEGIS python=3.10 -y
conda activate AEGIS
```

Next, pull all dependencies required for the engine (FastAPI, NetworkX, scikit-learn, WebSockets):
```bash
pip install -r requirements.txt
```

## 3. Starting the Attribution Engine

Navigate into the `backend` directory and launch Uvicorn. The engine immediately boots its 1.5-second asynchronous pipeline while opening a WebSocket channel for the React frontend.

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
*Expected Output:* `Application startup complete.` 
*(Note: Do not close this terminal. It continuously processes the 10,000-event telemetry load under the hood).*

## 4. Launch the Command Center

Navigate your browser directly to the Python backend's host port:
**[http://localhost:8000](http://localhost:8000)**

## 5. UI Operational Workflow

AEGIS is built across three primary functional panes, available at the top navigation bar:

1. **Overview Tab (The Live Radar):**
   * **What it shows:** An immediate, real-time map of node telemetry and trust degradation.
   * **How to use it:** Watch how nodes handle sequential anomalies. When the 60-second temporal cluster isolates the start of an infection, the UI will pinpoint and lock onto **P-ZERO**.

2. **Shadow Control Tab (The Conviction Dashboard):**
   * **What it shows:** The exact output of our internal `AttributionEngine`.
   * **How to use it:** This operates on a completely different premise than the Overview Map. Instead of tracking loud failures, it identifies the quiet *Shadow Controller* responsible for building lateral bridges and pushing downstream telemetry failures. Read the human-readable string below the top suspect to understand the mathematical justification. Click "Initiate Kill Switch" to simulate excising that node from the causality graph.

3. **Analytics (The Data Sweep):**
   * **What it shows:** The raw trajectory data tracking the sliding 60-tick window for average latency, load, and total anomaly count over time.

### Forensic Ledger
At the absolute top right of the dashboard, you will find the **HISTORY** button. This opens the SQLite-backed immutable logging ledger. Every single deviation, identity theft, and telemetry lie our reconstruction engine caught is recorded here with hard metadata, ready for SOC auditing.
