# Consistency Model

A paramount requirement in network security tools is absolute, unified consistency. It is critical that the live websocket alerts visually match the identical time-stamped elements rendered in the historical CSV data export.

AEGIS uses a rigid **Single Source Engine Architecture** to enforce mathematically flawless consistency.

## The Temporal Singularity
Because the entire backend architecture derives its truth layer purely from the `DatasetStreamer` linear cursor, there are no unresolvable states.
The exact index location `stream_cursor` acts as a singularity.
1. It reads exact row `X`.
2. It pushes standard math to construct a state.
3. If the math triggers penalties, exactly one process inserts into the database.
4. Exactly the same payload goes to the live WebSocket.

Therefore, an incident at timestamp `T` on the live radial map guarantees the exact same coordinates and math exist statically in the SQLite database, returning flawlessly when the user invokes the pagination APIs.

## Stale State Rejection
The node registry is not updated asynchronously relative to the stream pipeline. 
The `NodeState` classes operate directly across the primary execution loop.

When the `DatasetReconstructor` generates its `_build_node_snapshot()` structure, it does not query an intermediate caching layer (e.g., Redis). It pulls the active RAM attributes of the Python class inside the primary memory heap at that exact fraction of a second. This mechanism eliminates synchronization latency between data detection and visual reporting entirely.
If a Node's identity string fails validation, its `NodeState.current_trust` parameter collapses identically before the dictionary conversion process ever loops the event over to a consumer endpoint.

## The Problem With Time
The primary obstacle to data consistency in AEGIS lies in presentation rendering.
If the WebSocket delivers an array containing 42 unique anomalies inside an instantaneous batch update, standard browsers fail to render DOM objects (HTML elements) sequentially with absolute truth.

The UI mitigates this by abstracting the raw UI arrays into specific `<canvas>` geometry layers utilizing `requestAnimationFrame`. Plotted "history dots" pulled asynchronously via `/api/history` are mathematically joined to the rapidly shifting WebSocket data states via unique `node_id` parameters across dual state-lists in React, meaning a visual alert always mirrors the exact stored value regardless of which transport vector supplied the notification.

This guarantees that a forensic analyst querying history for "Node 32 identity theft" will see the identical data footprint that a live operator witnessed on the constellation map the moment the attack occurred.
