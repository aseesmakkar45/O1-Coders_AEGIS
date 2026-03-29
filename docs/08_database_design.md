# Database Design and Storage Management

AEGIS implements a deliberate storage model focused strictly on temporal logging. Rather than creating convoluted relational schemas, AEGIS uses a flat, event-driven ledger pattern optimized for rapid inserts and deep querying.

The database engine is built exclusively around **SQLite3**, deployed within the engine context (`HistoryDatabase.py`). 

## The Core Schema (`INCIDENT_HISTORY`)

The `INCIDENT_HISTORY` table is the sole source of truth for persistent anomalies. All data stored here has passed the multi-layer pipeline and mathematically triggered a trust drop.

### Table Definition

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key (Auto-Incrementing). |
| `timestamp` | TEXT | ISO Format. Exact temporal marker of the anomaly trigger. |
| `node_id` | TEXT | The origin ID of the anomaly. |
| `anomaly_type` | TEXT | Enum class (e.g. `LATENCY_SPIKE`, `IDENTITY_THEFT`). |
| `severity` | TEXT | `LOW`, `MEDIUM`, or `CRITICAL`. |
| `trust_before` | REAL | The node's 0-100 score immediately prior to the event. |
| `trust_after` | REAL | The node's 0-100 score immediately after penalty application. |
| `trust_delta` | REAL | The exact subtractive penalty calculated. |
| `http_status` | INTEGER | The raw wire transport code (e.g., `500`). |
| `json_status` | TEXT | The application payload (e.g., `OPERATIONAL`). |
| `schema_version` | TEXT | Active database schema version (e.g., `v2`). |
| `decoded_identity` | TEXT | De-obfuscated Base64 identity tag. |
| `propagation_source`| TEXT | (Optional) Origin node ID if the incident was lateral movement. |
| `latency_ms` | REAL | The specific response time at the moment of the event. |

## Concurrency Mechanics

To bridge asynchronous web-loops handling UI clients and the internal processing loops running at high concurrency, the sqlite3 connection employs:
`sqlite3.connect(..., check_same_thread=False, isolation_level=None)`

This bypasses the standard blocking transaction models. AEGIS handles single-thread writes natively via Python's Global Interpreter Lock (GIL) combined with `asyncio`, guaranteeing synchronous, thread-safe writes into the storage medium without dropping events.

## Debounce Filtering

A single `LATENCY_SPIKE` persisting for 15 seconds across a 6Hz ingestion loop would naively result in 90 identical rows.
The internal `insert_incident` method enforces a `debounce_window_sec` (Default: 2.0s). 
Before generating a direct `INSERT INTO`, the engine performs an `ORDER BY id DESC LIMIT 1` on the `node_id` and `anomaly_type`. If the delta time from the identical previous anomaly is beneath the threshold, the write is aborted, preserving database utility while acknowledging the incident in RAM.

## Bounded Disk Pruning

AEGIS does not permit unstructured disk bloat. 
The system defines a hard capacity ceiling at **10,000 rows**. 
If row counts breach this upper bracket, an automated pruning sequence executes periodically (`_check_prune()`).

```sql
DELETE FROM INCIDENT_HISTORY WHERE id NOT IN (
    SELECT id FROM INCIDENT_HISTORY ORDER BY id DESC LIMIT 10000
)
```

This ensures the SQLite file remains light enough for lightning-fast front-end pagination queries, effectively capping disk sizing without manual administrative cron jobs.
