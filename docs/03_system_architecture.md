# System Architecture

AEGIS is an event-driven system designed to analyze high-velocity network telemetry and attribute attacks. It operates within a 1.5-second tick cycle, processing raw events through a multi-layer verification pipeline and causal graph engine.

## Core Core Engines

- **DatasetStreamer**: Batches network events from CSV files for real-time simulation.
- **DatasetReconstructor**: Handles trust scoring and anomaly detection based on verification layers.
- **GraphEngine**: Builds an anomaly directed graph as lateral movement and causality occur.
- **FeatureEngine**: Generates behavioral vectors for isolation forest analysis.
- **AttributionEngine**: Fuses five signals to rank and identify potential shadow controllers.

## Persistence and Output

- **SQLite HistoryDB**: Logs trust events and anomalies with debouncing and record pruning.
- **WebSocket Broadcast**: Sends real-time state updates to the React dashboard.
- **REST History API**: Powers historical queries for the Forensic Ledger.

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Graph Engine**: NetworkX, NumPy
- **ML Engine**: scikit-learn
- **Database**: SQLite3
- **Frontend**: React 18, D3.js, Chart.js
