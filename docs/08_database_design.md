# Database Design and Storage Management

AEGIS uses an embedded SQLite3 database for persistent forensic logging. The design is intentionally flat — a single event-driven table optimized for rapid inserts and flexible querying. There are no complex relational joins. Every row represents one processed telemetry event with its full context.

The database engine lives in `database/history_db.py` and is instantiated by the `DatasetReconstructor` at startup.

## Schema: `INCIDENT_HISTORY`

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Auto-incrementing primary key |
| `timestamp` | TEXT | ISO 8601 format — when the event was processed |
| `node_id` | TEXT | The node that generated this event |
| `anomaly_type` | TEXT | Classification: `IDENTITY_THEFT`, `DDOS_ATTACK`, `GHOST_NODE`, `LATENCY_SPIKE`, `SCHEMA_ROTATION`, or `NORMAL_TRAFFIC` |
| `severity` | TEXT | `CRITICAL`, `MEDIUM`, `LOW`, or `0` (normal) |
| `trust_before` | REAL | Trust score immediately before this event |
| `trust_after` | REAL | Trust score immediately after penalty application |
| `trust_delta` | REAL | Computed difference (trust_after - trust_before) |
| `http_status` | INTEGER | Raw HTTP response code (200, 206, 429, 500, etc.) |
| `json_status` | TEXT | Application-layer payload status (e.g., `OPERATIONAL`) |
| `schema_version` | TEXT | Active schema version at time of event (e.g., `v2`) |
| `decoded_identity` | TEXT | De-obfuscated Base64 identity string |
| `latency_ms` | REAL | Response time in milliseconds at the moment of the event |

**Important:** Every event gets logged — not just anomalies. Normal traffic events are recorded with `anomaly_type = NORMAL_TRAFFIC` and `severity = 0`. This gives analysts a complete picture of a node's timeline, including the quiet periods between attacks.

## Concurrency Model

The SQLite connection uses `check_same_thread=False` and `isolation_level=None` to support writes from the async simulation loop without blocking. Python's Global Interpreter Lock (GIL) combined with `asyncio`'s cooperative scheduling guarantees that only one write operation executes at a time, providing effective thread safety without explicit locking.

## Debounce Filtering

Without filtering, a sustained latency spike across a 6-event batch running at 1.5-second intervals would generate dozens of identical log entries per minute. The `insert_incident` method enforces a debounce window (default: 2.0 seconds):

1. Before inserting, it queries the most recent row matching the same `(node_id, anomaly_type)` pair.
2. If the time delta from that row is less than the debounce threshold, the write is silently skipped.
3. Anomalous events still affect trust scores and attribution in memory — only the database write is suppressed.

This keeps the forensic log useful without flooding it with redundant entries.

## Auto-Pruning

To prevent unbounded disk growth, the database enforces a hard cap of **10,000 rows**. A periodic pruning check removes the oldest entries beyond this limit:

```sql
DELETE FROM INCIDENT_HISTORY WHERE id NOT IN (
    SELECT id FROM INCIDENT_HISTORY ORDER BY id DESC LIMIT 10000
)
```

This runs automatically during high-volume ingestion periods, keeping the SQLite file small enough for fast pagination queries without manual intervention.

## Query Interface

The `HistoryDatabase` class exposes several query methods consumed by the REST API:

- **`query_history(limit, offset, node_id, anomaly_type, severity, date_filter, time_chunk)`** — Flexible multi-filter pagination query. Supports filtering by node, anomaly type, severity level, date, and time window.
- **`get_summary()`** — Aggregate statistics: total incidents, critical count, and top anomaly vector. Used by the executive dashboard metrics.
- **`clear_history()`** — Wipes the entire table for fresh demonstrations.

## CSV Export

The `GET /api/export/history` endpoint reads from the database with the same filter parameters, formats the results as CSV with proper headers and quoting, writes to a temporary file, and returns it as a `FileResponse` download. The frontend also supports a two-step export flow via `POST /api/export/prepare` for client-generated CSV content.
