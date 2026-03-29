# API and Real-Time Transport 

AEGIS provides full data extraction paths. A sophisticated frontend only matters if the foundational API surfaces are predictable.
The system relies on a unified FastAPI namespace containing both historical REST endpoints and the bi-directional WebSocket implementation.

## 1. REST Architecture 

### Temporal Navigation
`POST /api/seek/{position}`
- **Purpose**: Binds the global temporal timeline back/forward.
- **Parameters**: `position` (int). Linear row index from the active datastore.
- **Side Effect**: Automatically invokes `reconstructor.reset()`, forcefully zeroing node-state dictionaries and triggering frontend dashboard hard resets.

`POST /api/seek_event/{anomaly_type}`
- **Purpose**: Search the datastore linearly until the specific threat criteria matches, then trigger `ANOMALY_BURST` transmission.
- **Parameters**: `anomaly_type` (Enum String: `LATENCY_SPIKE`, `DECEPTIVE_TELEMETRY`, `IDENTITY_THEFT`).

### Extraction and Deep-Dive
`GET /api/history`
- **Purpose**: Returns bounded historical data from the `INCIDENT_HISTORY` SQLite backend.
- **Query Params**:
  - `limit`: Row truncation (Default: 50)
  - `offset`: Pagination offset.
  - `node_id`: Target a specific machine.
  - `anomaly_type`: Filter to specific events.
  - `date_filter`: Bounds queries by YYYY-MM-DD keys.
- **Returns**: Array of fully hydrated historical records.

`GET /api/history/summary`
- **Purpose**: Broad network aggregations intended for executive components. Returns `total_incidents`, `critical_incidents`, and the mathematically highest `top_anomaly_vector` across the active lifecycle.

`GET /api/export/history`
- **Purpose**: Forces total data aggregation, formatting, and file-writing into a highly compliant CSV. Pushes a native `.csv` download stream via `FileResponse` to the client.

## 2. WebSocket Real-Time Interface

The core transport protocol. Every UI dashboard requires active connection to `ws://[HOST]:8000/ws`.

### The Payload Architecture
Every 1.5 seconds, the server broadcasts an immense serialized dictionary containing:

```json
{
    "nodes": [
        {
            "node_id": "84",
            "trust_score": 100.0,
            "raw_telemetry": {
                "json_payload": {"status": "OPERATIONAL"},
                ...
            },
            ...
        }
    ],
    "new_logs": [ ... ],
    "patient_zero": {
        "patient_zero_node": "31",
        "confidence": 85,
        "linked_nodes": ["91", "2"]
    },
    ...
}
```

### Protocol Mechanics
- **Connection Trap**: Upon connecting (`await websocket.accept()`), the server interprets this as a fresh session initiation. It forcefully zeroes the temporal timeline `streamer.seek(0)` and performs a server-side state reset. This mechanism ensures perfect synchrony immediately upon new user connection.
- **Client Handling**: Dead connections throwing `WebSocketDisconnect` are securely managed inside isolated try/except wrappers inside `dead_clients` lists, allowing indefinite scalability.
