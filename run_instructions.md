# AEGIS System Run Instructions

AEGIS is a self-contained system with zero frontend build steps. The backend serves the dashboard directly — no `npm install` or separate frontend server required.

## Prerequisites
* **Python 3.10** (recommended via Conda or any virtual environment manager)
* A modern web browser (Chrome, Edge, or Firefox)

## 1. Create the Environment
From the project root:
```bash
conda create -n AEGIS python=3.10 -y
conda activate AEGIS
```

## 2. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn`, `websockets`, `pydantic`, `python-multipart`, `numpy`, `networkx`, `scikit-learn`, `scipy`.

## 3. Start the AEGIS Core Engine
Navigate into the backend directory and launch:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

> **Wait for:** `Application startup complete.`
> Do not close this terminal — the simulation loop and WebSocket engine run inside this process.

## 4. Open the Dashboard
Navigate to:
```
http://localhost:8000
```

The backend serves the complete frontend directly from `frontend/index.html`. No separate frontend server is needed.

## 5. Using the Dashboard

1. **Auto-Reset:** Opening the dashboard automatically resets the simulation to position 0. The dataset streams from the beginning every time a new tab connects.

2. **Overview Tab:** Watch real-time node telemetry, trust scores, Patient Zero identification, and the Forensic Radar Map. The system status header flips to "UNDER ATTACK" when anomalies cascade.

3. **Shadow Control Tab:** Navigate here to see the 5-signal attribution engine in action. The ranked suspect panel shows the Shadow Controller with full signal breakdowns (Propagation, Bridge, Anomaly, Stability) and human-readable reasoning.

4. **Analytics Tab:** Trust deviation charts, latency/anomaly trends, and a live intelligence stream showing every processed event.

5. **History (Forensic Ledger):** Click the "HISTORY" button in the top header. The SQLite-backed ledger shows every logged incident with full metadata, filterable by node, severity, anomaly type, and date.

6. **Pause/Resume:** Click the red STOP button to pause the simulation without disconnecting the WebSocket. Click again to resume.

7. **Dark Mode:** Toggle via the top-right button for the military-grade command interface aesthetic.

8. **Restart Demo:** Click "RESTART DEMO" to flush all memory state and reset the dataset cursor to 0.

9. **Kill Switch:** In the Shadow Control tab, click any node on the attack graph and press "INITIATE KILL SWITCH" to simulate quarantining a suspected attacker.
