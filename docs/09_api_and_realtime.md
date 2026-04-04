# API and Real-Time Transport

AEGIS exposes a unified API surface through FastAPI: REST endpoints for historical queries and operational control, attribution endpoints for threat intelligence, and a WebSocket interface for real-time state streaming.

## REST Endpoints

### Dataset Navigation

**`POST /api/seek/{position}`**
Jumps the dataset cursor to a specific row index. Triggers a full engine reset — all in-memory node states, graph windows, feature histories, and Patient Zero tracking are wiped. The dashboard starts fresh from the new position.

**`POST /api/seek_event/{anomaly_type}`**
Scans forward in the dataset until a row matching the specified anomaly type is found. Supported types: `LATENCY_SPIKE`, `DECEPTIVE_TELEMETRY`, `IDENTITY_THEFT`, `SCHEMA_ROTATION`. Returns the target position on success.

### Attribution and Threat Intelligence

**`GET /api/detect`**
Returns the current top 10 Shadow Controller suspects, ranked by the 5-signal attribution score. Each suspect object contains:
- `node_id` — The suspected node
- `final_score` — Composite attribution score [0, 1]
- `breakdown` — Individual signal scores: `propagation`, `betweenness`, `centrality` (diagnostic only), `pagerank`, `anomaly`, `frequency`, `stability`
- `reasoning` — Array of human-readable explanations

**`GET /api/metrics`**
Returns engine diagnostics: current tick count, tracked node count, and active propagation edge count.

### Operational Control

**`POST /api/toggle_pause`**
Pauses or resumes the simulation loop. WebSocket connections remain open — the dashboard simply stops receiving new data until resumed.

**`POST /api/simulate/remove_node/{node_id}`**
Kill Switch simulation. Removes the target node from the graph engine (drops all edges and event window entries) and excludes it from future attribution scoring. The node remains in the Reconstructor's memory but is flagged as killed.

### Historical Forensics

**`GET /api/history`**
Paginated query against the SQLite `INCIDENT_HISTORY` table.
- `limit` (default: 50) — Maximum rows to return
- `offset` (default: 0) — Pagination offset
- `node_id` — Filter by specific node
- `anomaly_type` — Filter by anomaly classification
- `severity` — Filter by severity level
- `date_filter` — Filter by date (YYYY-MM-DD)
- `time_chunk` — Filter by time window

**`GET /api/history/summary`**
Aggregate statistics for executive dashboard metrics: total incidents, critical count, and dominant anomaly vector.

**`GET /api/history/node/{node_id}`**
Chronological event history for a single node (default limit: 50).

**`GET /api/export/history`**
Generates a CSV export of filtered history data and returns it as a file download via `FileResponse`.

**`POST /api/export/prepare`** + **`GET /api/export/file/{file_id}/{filename}`**
Two-step export flow for client-generated CSV content. The frontend posts CSV text, receives a download URL, then fetches the file.

**`DELETE /api/history/clear`**
Wipes the entire `INCIDENT_HISTORY` table. Used for clean demonstration restarts.

### Diagnostics

**`GET /api/debug`**
Comprehensive health check: simulation loop status, tick count, last error, streamer position, total events, registry size, connected client count, pause state, and reconstructor state.

**`GET /api/dataset/info`**
Dataset statistics: total events, current cursor position, batch size, and pause state.

---

## WebSocket Real-Time Interface

The primary data transport. Every dashboard connects to `ws://[HOST]:8000/ws` for live state streaming.

### Connection Lifecycle
1. **On connect:** The server accepts the WebSocket upgrade, adds the client to `clients[]`, resets the simulation to position 0, and resumes playback. This ensures every new browser tab gets a clean, synchronized demo start.
2. **During session:** The server broadcasts the full system state to all clients every 1.5 seconds.
3. **On disconnect:** `WebSocketDisconnect` exceptions are caught, and the dead client is removed from `clients[]`. No blocking cascade occurs.

### Payload Structure
Every broadcast sends a JSON object containing the complete system state:

```json
{
    "nodes": [
        {
            "node_id": "84",
            "trust_score": 72.3,
            "raw_telemetry": {
                "json_payload": {"status": "OPERATIONAL"},
                "http_status": 200,
                "latency": 0.142,
                "schema_version": "v2",
                "load_value": 0.45,
                "active_column": "load_val"
            },
            "decoded_identity": "node-084",
            "is_infected": true,
            "anomalies": ["LATENCY_SPIKE"]
        }
    ],
    "new_logs": [ ... ],
    "patient_zero": {
        "patient_zero_node": "412",
        "confidence": 85,
        "linked_nodes": ["91", "2"]
    },
    "attribution_suspects": {
        "57": {
            "node_id": 57,
            "final_score": 0.655,
            "breakdown": {
                "propagation": 0.583,
                "betweenness": 1.0,
                "centrality": 0.417,
                "pagerank": 0.541,
                "anomaly": 0.24,
                "frequency": 0.224,
                "stability": 1.0
            },
            "reasoning": ["Acts as a primary structural bridge for lateral movement."],
            "confidence": 0.312
        }
    },
    "propagation_graph": [
        {"source": "57", "target": "182", "weight": 0.83}
    ],
    "forensic_edges": [ ... ],
    "propagation_edges": 24,
    "latest_tick_trust": 42.1,
    "tick_events": [ ... ],
    "metrics": {
        "latency_series": [ ... ],
        "anomaly_series": [ ... ],
        "attack_vectors": {
            "IDENTITY_THEFT": 2,
            "LATENCY_SPIKE": 5,
            "SCHEMA_ROTATION": 3,
            "DDOS_ATTACK": 1,
            "GHOST_NODE": 0
        },
        "latest_incident": { ... }
    },
    "dataset_position": 1200,
    "total_events": 10000,
    "total_registry_nodes": 100,
    "stream_mode": "SEQUENTIAL"
}
```

### Key Payload Fields
- **`nodes`** — Current snapshot of every tracked node with trust, telemetry, identity, and anomaly data.
- **`attribution_suspects`** — Full attribution breakdown for every node in the causal graph, keyed by node_id.
- **`propagation_graph`** — All edges in the causal graph with weights (for the Shadow Control visualization).
- **`forensic_edges`** — Top 50 strongest edges (for the overview map).
- **`patient_zero`** — Current Patient Zero identification with confidence and linked nodes.
- **`metrics`** — Rolling time series for latency, anomaly counts, and attack vector totals.
