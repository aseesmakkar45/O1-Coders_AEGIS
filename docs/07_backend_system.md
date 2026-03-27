# Backend System Overview

The AEGIS backend is a FastAPI monolith written in Python 3.10+. It uses an asynchronous simulation loop to ingest and process network events in real-time.

## Key Modules

- **`main.py`**: The entry point for the FastAPI server and WebSocket state broadcaster.
- **`simulation/dataset_streamer.py`**: Reads and batches network events from CSV files.
- **`engine/reconstructor.py`**: Processes raw event data for trust scoring and anomaly detection.
- **`engine/graph_engine.py`**: Manages the directed graph of causal anomalies and causal links.
- **`engine/attribution_engine.py`**: Fuses graph and behavioral signals for suspect ranking.
- **`database/history_db.py`**: Provides asynchronous persistence for forensic events via SQLite3.

## Operation

1. The `DatasetStreamer` pulls a batch of events from the CSV data source.
2. The `DatasetReconstructor` validates each event and increments/decrements node trust scores.
3. If an event is anomalous, the `GraphEngine` adds it to the sliding window of causal edges.
4. The `AttributionEngine` recalculates current suspect rankings and Shadow Controller candidates.
5. The full updated state is broadcast to all connected WebSocket clients every 1.5 seconds.
