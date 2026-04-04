# Backend System and Execution Model

The AEGIS backend is a FastAPI application that serves as both the web server and the real-time simulation engine. It reads telemetry from static CSV files, processes events through a multi-layer verification and attribution pipeline, persists results to SQLite, and streams the full system state to connected dashboards via WebSocket.

## Module Structure

```
backend/
├── main.py                          # FastAPI entrypoint, simulation loop, API routes
├── simulation/
│   └── dataset_streamer.py          # CSV ingestion, batching, Base64 decoding
├── engine/
│   ├── dataset_reconstructor.py     # Core state machine: trust scoring, event routing
│   ├── attribution_engine.py        # Shadow Controller scoring (5-signal fusion)
│   ├── graph_engine.py              # Sliding-window causal graph (200 events)
│   ├── feature_engine.py            # Per-node behavioral vector extraction (5D)
│   ├── patient_zero.py              # Temporal anomaly clustering, origin detection
│   └── logger.py                    # Alert log emission
├── config/
│   └── attribution_config.py        # Tunable weights and solver constraints
├── database/
│   └── history_db.py                # SQLite persistence, debouncing, pruning
└── scripts/
    └── reorder_csv.py               # Dataset preprocessing utility
```

## The FastAPI Scaffold (`main.py`)

The entrypoint is an asynchronous FastAPI app running inside `uvicorn`. It handles three responsibilities concurrently:

**1. HTTP Request Handling.**
FastAPI and Uvicorn manage incoming REST requests for history queries, dataset navigation, attribution lookups, and serving the frontend HTML.

**2. WebSocket Management.**
The `websocket_endpoint` accepts upgrade requests and maintains a `clients[]` list. On connection, the server resets the simulation to position 0 for a clean demo start. Dead connections are cleaned up via `WebSocketDisconnect` exception handling.

**3. The Simulation Loop.**
At startup (`@app.on_event("startup")`), an `asyncio.create_task(simulation_loop())` is launched. This task fires every 1.5 seconds, pulls a batch from the streamer, processes it through the Reconstructor, and broadcasts the result to all connected WebSocket clients. The `await asyncio.sleep(1.5)` yields execution between ticks, ensuring the web server remains responsive.

## Engine Orchestration

The `DatasetReconstructor` is the central coordinator. Each tick it:

1. Processes ~6 events through the Layer 0-4 verification pipeline, applying trust penalties.
2. Feeds **every** event (anomalous or not) into the `FeatureEngine` for behavioral profiling.
3. Feeds **anomalous** events into the `GraphEngine`'s sliding window (last 200 anomaly events).
4. Records identity theft edges in the `GraphEngine` when spoofing is detected.
5. Logs every event to the SQLite `INCIDENT_HISTORY` table (with debounce filtering).
6. Calls `AttributionEngine.execute_attribution()`, which:
   - Rebuilds a causal `nx.DiGraph` from the sliding window.
   - Computes 5 scoring signals: Propagation, Betweenness, PageRank, ML Anomaly, Frequency.
   - Computes Closeness Centrality for diagnostic display (excluded from final score).
   - Applies stability boosting from PageRank variance history.
   - Applies dominance boost for nodes dominant in both Propagation and Betweenness.
   - Returns ranked suspects with full score breakdowns and reasoning arrays.
7. Serializes the full system state — node snapshots, logs, attribution suspects, graph edges, Patient Zero data, metrics — and broadcasts via WebSocket.

## Memory Architecture

The backend maintains a **hot-state** memory model. The `DatasetReconstructor` holds a `self.nodes = {}` dictionary mapping `node_id` to `NodeState` objects. These objects track:

- `current_trust` — Rolling trust score (0-100)
- `ewma_latency` — Exponentially weighted moving average of response times
- `std_dev` — Standard deviation baseline for Z-score calculations
- `original_identity` — The first decoded identity seen for this node
- `last_schema` — The last schema version received from this node
- `last_anomaly_time` — Tick of the most recent anomaly
- `anomaly_count` — Cumulative anomaly counter

All validation computations happen against this in-memory state. The database is used exclusively for persistent logging — never for live lookup or validation. This keeps per-event processing under a millisecond.

## Dataset Navigation

Because AEGIS runs on a static dataset, it provides temporal navigation controls:

- **`seek(position)`:** Jumps the dataset cursor to a specific row index. Triggers a full `reconstructor.reset()`, wiping all in-memory state (NodeStates, GraphEngine window, FeatureEngine histories, PatientZeroTracker). The dashboard restarts cleanly from the new position.
- **`seek_event(anomaly_type)`:** Scans forward in the dataset until it finds a row matching the requested anomaly criteria (e.g., LATENCY_SPIKE, IDENTITY_THEFT). Useful for jumping directly to demonstration scenarios.

## Kill Switch Simulation

The `POST /api/simulate/remove_node/{node_id}` endpoint drops a node from the graph engine, removing all associated identity edges and event window entries. The node is excluded from future attribution scoring. This simulates quarantine — analysts can observe how the network's threat topology changes when the suspected controller is removed.

## Crash Resilience

The simulation loop is wrapped in a broad try/except that logs errors without killing the process. WebSocket disconnections are handled gracefully — dead clients are removed from the `clients[]` list during each broadcast cycle, preventing blocking cascades on future sends. The `loop_status` dictionary tracks running state, tick count, last error, and client count for diagnostics via the `GET /api/debug` endpoint.
