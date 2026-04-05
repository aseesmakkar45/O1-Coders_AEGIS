# Consistency Model

In a security tool, consistency isn't a nice-to-have — it's a hard requirement. If the live dashboard shows an identity theft event on Node 57 at 14:32:01, the forensic database query for Node 57 must return the exact same event with the exact same trust values. AEGIS enforces this through a single-source architecture where no data path can diverge.

## Single Source of Truth

The entire system derives its state from one place: the `DatasetReconstructor`'s in-memory `NodeState` dictionary, fed by the `DatasetStreamer`'s linear cursor.

Here's why divergence is impossible:

1. The streamer reads row X from the dataset.
2. The Reconstructor processes row X through its verification layers, computing trust penalties.
3. If penalties are applied, the event is logged to SQLite *and* added to the WebSocket broadcast payload — in the same function call, from the same computed values.
4. The `_build_node_snapshot()` method reads directly from the live `NodeState` object in RAM — there is no intermediate cache, no delayed queue, no eventual consistency model.

A trust score displayed on the dashboard at time T is mathematically identical to the trust score written to the database at time T because both values are read from the same Python object in the same execution frame.

## No Stale State

The `NodeState` objects are updated synchronously within the main processing loop. When `process_event()` modifies `node.current_trust`, that modification is immediately visible to:
- The `_build_node_snapshot()` call that serializes the state for WebSocket broadcast
- The `insert_incident()` call that persists the trust_before and trust_after values to SQLite
- The `AttributionEngine` that reads node states for the current tick's scoring

There is no asynchronous update queue where writes could be reordered or delayed. Python's GIL ensures that the single-threaded event processing completes atomically before the state is serialized and sent.

## Attribution Consistency

The attribution suspects included in the WebSocket payload are computed at the end of `process_batch()` — after all events in the tick have been processed and all trust scores have been finalized. This means:
- The graph edges used for attribution reflect the current tick's anomalies.
- The feature vectors used for Isolation Forest scoring include the current tick's telemetry.
- The suspect rankings displayed on the Shadow Control panel are synchronized with the node trust scores shown on the Overview panel.

## Frontend Synchronization

The dashboard receives the entire system state in a single JSON payload every 1.5 seconds. All six views (Overview, Analytics, Shadow Control, etc.) render from the same `currentState` object, selected via React's `useMemo`. This eliminates the possibility of one panel showing data from tick N while another shows tick N-1.

The Radar Map merges two data sources — live WebSocket events and historical dots from `/api/history` — but both originate from the same Reconstructor pipeline. A dot plotted from a WebSocket tick and the same incident retrieved from SQLite will have identical node IDs, timestamps, anomaly types, and trust values because they were written by the same `process_event()` call.

## The Practical Guarantee

A forensic analyst querying the history for "Node 57 — IDENTITY_THEFT" will find the exact same data that a live operator saw on the dashboard when the attack occurred. The trust drop, the decoded identity, the HTTP status, the latency — every field matches because there is exactly one computation path, and both the live stream and the persistent store are downstream consumers of that single path.
