# AEGIS System Run Instructions

The AEGIS dataset-driven architecture is engineered to run seamlessly out of the box with zero complex UI deployment steps. Follow the commands strictly below.

## Prerequisites
* **Python 3.9+**
* An active Conda/Venv environment is recommended but not strictly required.
* Ensure you navigate your terminal into the root project folder `/rosetta`.

## 1. Install Backend Dependencies
From the root `/rosetta` folder, install the required packages:
```bash
pip install fastapi uvicorn websockets pydantic
```

## 2. Start the AEGIS Core Engine
Navigate directly into the backend directory and spin up the Uvicorn execution loop.
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
> [!TIP]
> **Wait for the prompt:** `Application startup complete.`
> Do not close this terminal! The simulation and WebSocket engine are tethered to this process.

## 3. Launch the Dashboard
Open your preferred modern web browser (Chrome, Edge, Firefox) and navigate to the local node:
```
http://localhost:8000
```

## 4. Initiating the Demo Flow
1. **Initial Access:** Upon load, the dashboard will immediately connect to the backend, trigger a hard reset to position `0`, and stream live anomaly data sequentially.
2. **Review Ledger:** Click the `HISTORY` button in the upper right. The SQLite module creates `aegis_history.db` dynamically to begin forensic extraction. 
3. **Execution Controls:** Click the red `STOP` square button to cleanly pause the backend stream without severing the websocket connection.
4. **Trigger Injections:** Click `Ghost Node`, `Identity Theft`, or `Spike DDoS` manually to warp the master datasets timeline into complex hack vectors.
5. **Restart:** Hit `RESTART DEMO` to flush memory trackers uniformly.
