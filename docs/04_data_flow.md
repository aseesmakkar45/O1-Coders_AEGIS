# Data Flow and State Progression

Understanding AEGIS means understanding the journey of a single piece of telemetry — from a CSV row to a trust penalty to a Shadow Controller conviction to a pixel on the dashboard. This document traces that entire path.

## The Pipeline Lifecycle

### Phase 1: Ingestion and Joining
1. The `asyncio` simulation loop in `main.py` fires every 1.5 seconds.
2. It calls `streamer.get_batch()`, which reads the next 6 rows from `system_logs.csv`.
3. The streamer cross-references each `node_id` against `node_registry.csv` to fetch the raw User Agent string.
4. It decodes the Base64 signature embedded in the User Agent to establish the node's **hardware identity**.
5. It maps the event's timeline position against `schema_config.csv` to determine the expected schema version.
6. A complete, un-sanitized `event` dictionary is constructed with all fields: `node_id`, `http_response_code`, `json_status`, `response_time_ms`, `load_value`, `decoded_id`, `schema_version`, `log_id`, and `is_infected`.

### Phase 2: Reconstruction and Trust Scoring
1. The batch is passed to `reconstructor.process_batch(events)`.
2. For each event, the Reconstructor retrieves (or creates) the node's `NodeState` from its in-memory dictionary.
3. The event passes through four verification layers in priority order:
   - **Ghost Node Trap:** Is `node_id >= 500`? If yes, apply -40 to -50 penalty.
   - **Identity Check:** Does the `decoded_id` belong to a different node in the ownership ledger? If yes, flag IDENTITY_THEFT (-100 penalty), record an identity edge in the `GraphEngine`.
   - **Schema Check:** Has the `schema_version` changed since this node's last event? If yes, flag SCHEMA_ROTATION (-10 to -15).
   - **Latency/DDoS Check:** Is the Z-score of `response_time_ms` against the EWMA baseline > 3.0? If yes, check `load_value`. Above 0.85 = DDOS_ATTACK (-45 to -60). Below 0.85 = LATENCY_SPIKE (-15 to -25).
4. **Trust Update:** Penalties are subtracted from the node's trust score (clamped to 0-100). If no penalties are applied and the last anomaly was more than 3 ticks ago, trust recovers by +2.0.

### Phase 3: Attribution Pipeline
When a penalty is applied during Phase 2, three things happen in parallel:

1. **Graph Recording:** The anomaly event (`node_id`, `log_id`) is pushed into the `GraphEngine`'s sliding window deque (capacity: 200). Identity theft edges are recorded separately with high weight (1.2).
2. **Feature Extraction:** The `FeatureEngine` updates the node's behavioral vector from the raw event telemetry (latency, load, HTTP status, tick time). This happens for *all* events, not just anomalous ones.
3. **Patient Zero Tracking:** The anomaly is logged into the `PatientZeroTracker` for temporal cluster analysis.

At the end of `process_batch`, the `AttributionEngine.execute_attribution()` is called:
- The `GraphEngine` rebuilds a fresh `nx.DiGraph` from its sliding window — temporal edges for anomalies within 1-3 log entries, plus identity theft edges.
- Five signals are computed: Propagation (outgoing edge weight sum), Betweenness Centrality, PageRank, IsolationForest anomaly score, and Frequency (normalized degree).
- Closeness Centrality is computed for diagnostic purposes but excluded from the final score.
- Stability boosting is applied from PageRank variance history (20-tick window).
- A dominance boost (+0.05) is applied to nodes scoring ≥0.7 in both Propagation and Betweenness.
- The top-scoring node is identified as the Shadow Controller. A confidence metric (score gap between #1 and #2) is attached.

### Phase 4: Persistence
Every event — anomalous or normal — is logged to the SQLite `INCIDENT_HISTORY` table:
1. A severity label is assigned: penalty ≥ 45 = CRITICAL, ≥ 25 = MEDIUM, > 0 = LOW, 0 = NORMAL_TRAFFIC.
2. The debounce filter checks if an identical `(node_id, anomaly_type)` pair was logged within the last 2.0 seconds. If so, the write is skipped.
3. The event is persisted with full telemetry: trust before/after, HTTP status, JSON status, schema version, decoded identity, and latency.

### Phase 5: Patient Zero Synthesis
1. The `PatientZeroTracker` prunes any anomaly older than 60 ticks from its active window.
2. If at least 2 anomalies remain, it identifies Patient Zero as the node with the oldest timestamp in the cluster.
3. A confidence score is computed from anomaly count (×10, max 40), identity theft presence (+35), and unique node spread (×12, max 25).
4. Confidence smoothly approaches the target: max +8/tick when rising, max -2/tick when falling.
5. If confidence reaches 0, the Patient Zero state clears entirely.

### Phase 6: Broadcast
1. The Reconstructor serializes its state: converting every `NodeState` into a JSON snapshot with trust scores, raw telemetry, decoded identity, infection status, and anomaly flags.
2. It attaches: attribution suspects (with full breakdowns and reasoning), propagation graph edges (all + top 50 forensic edges), Patient Zero cluster data, latency/anomaly time series, attack vector counts, and the latest incident.
3. FastAPI pushes this payload to every connected WebSocket client via `send_json`.
4. The React frontend distributes the payload across six dashboard views.
5. The cycle completes. 1.5 seconds later, it fires again.
