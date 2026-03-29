# Data Flow and State Progression

Understanding AEGIS demands understanding the journey of a single piece of telemetry. AEGIS is fundamentally a deterministic pipeline. A row from a dataset is converted into an event, stripped of its obfuscation, penalized mathematically, logged permanently, and broadcast globally.

This document maps the exact chronological flow of an event tick.

## The Pipeline Lifecycle

### Phase 1: Ingestion & Joining
1. The global `asyncio` simulation loop triggers inside `main.py` every 1.5 seconds.
2. It requests a batch of data via `streamer.get_batch()`.
3. The `DatasetStreamer` reads the next 6 rows from `data.csv`.
4. It cross-references `node_id` with `node_registry.csv` to fetch the raw User Agent.
5. It decodes the Base64 signature embedded in the User Agent to establish the **hardware identity**.
6. It maps the timeline to `schema_config.csv` to determine what schema version should be running right now.
7. A complete, un-sanitized `event` dictionary is constructed.

### Phase 2: Reconstruction & Penalization
1. The batch is passed immediately to `reconstructor.process_batch(events)`.
2. For every event, the Engine requests the current memory-state of the node (`NodeState`).
3. **Ghost Trap:** Is the `node_id >= 500` target threshold? If so, apply penalty.
4. **Identity Check:** Does the decoded identity exist? Has this identity been seen on a different node before? If so, flag **IDENTITY_THEFT**, draw a propagation edge graph, apply severe penalty.
5. **Schema Check:** Has the schema version unexpectedly mutated since the previous heartbeat? If so, flag **SCHEMA_ROTATION**, apply penalty.
6. **Latency/DDoS Check:** Does the response time wildly exceed the active Exponentially Weighted Moving Average (EWMA)? If so, query the `load_val`. High load + High latency = **DDOS_ATTACK**. Normal load + High latency = **LATENCY_SPIKE**. Apply appropriate severity penalties.
7. **Trust Calculation:** The severity penalties are subtracted from the node's rolling trust score (0 to 100). If no penalties occurred in the last 3000ms, the node naturally heals by `+2.0` trust.

### Phase 3: Persistence
Every time a penalty is applied and trust drops:
1. The event is mapped to a `"severity"` (LOW, MEDIUM, CRITICAL) based on the raw point drop.
2. The Database Engine (`insert_incident`) validates the event against the debounce window (preventing 100 logs per second for the same latency spike on the same node).
3. Allowed incidents are forcefully persisted directly into `INCIDENT_HISTORY`.

### Phase 4: Cluster Synthesis
1. All anomalies flagged during this tick are routed into the `PatientZeroTracker`.
2. The Tracker dumps any anomaly older than 60 seconds.
3. It recursively groups the events, finding the exact oldest event in the cluster.
4. An origin, propagation list, and confidence score are finalized.

### Phase 5: Exfiltration & Rendering
1. The `DatasetReconstructor` dumps its memory blocks back to JSON: converting every `NodeState` into a serializable snapshot.
2. It attaches the global latency series, the Patient Zero cluster data, and the newly generated database logs.
3. The FastApi router pushes this vast payload down the WebSocket pipe `await c.send_json(state)` to every dashboard connected.
4. The React Frontend catches the payload.
5. **Radar Map:** The frontend pulls the exact timestamp of the anomalies, mapping them geometrically to a 24-hour canvas circle.
6. **Heatmap:** Nodes under 80% trust glow red or pulse purple (Sleepers). 
7. The cycle completes. Exactly 1.5 seconds later, it fires again.
