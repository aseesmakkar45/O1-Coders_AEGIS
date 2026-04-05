# Scalability and Known Limits

AEGIS is designed as a high-fidelity forensic demonstration system. While the architecture is production-informed, it operates within specific engineering boundaries that are important to understand. This document is honest about what those boundaries are.

## Throughput

### Ingestion Rate
The simulation loop processes **6 events per 1.5-second tick** — roughly 4 events/second sustained. This rate is intentionally conservative: it keeps the dashboard visually readable and gives the attribution engine enough time per tick to rebuild the causal graph and run Isolation Forest scoring.

Pushing the batch size significantly higher (e.g., 600 events/tick) would not break the backend math, but it would overwhelm the frontend's D3 force simulation and canvas rendering, causing frame drops and unreadable visualizations.

### Graph Computation

The Isolation Forest fit/predict on ~100 nodes with 5-dimensional vectors is similarly fast, completing in single-digit milliseconds.

### WebSocket Broadcasting
The server iterates over a simple `clients[]` list for each broadcast. This works well for 1-10 concurrent dashboards. For hundreds of concurrent consumers, a pub/sub architecture (e.g., Redis channels with dedicated WebSocket termination workers) would be needed. The current design prioritizes simplicity for demonstration scenarios.

## Mathematical Assumptions

### EWMA Baseline
The latency detector uses an EWMA with `alpha = 0.15`, which means it takes roughly 20 events for the baseline to adapt to a new normal. The initial `std_dev` is anchored at `30.0`. This means:
- During the first ~20 events for a new node, the baseline may not accurately reflect the node's true latency profile.
- A node that starts under heavy load will have a skewed baseline until enough clean events arrive to decay it back.

### Patient Zero Window
The `PatientZeroTracker` uses a 60-tick sliding window. Attacks that unfold slowly over hours — with individual anomalies spaced more than 60 ticks apart — will not be clustered into a single Patient Zero identification. The system is optimized for detecting cascading failures that propagate within minutes, not slow-burn campaigns spanning days.

### Graph Causality
Temporal causal edges are inferred from log_id proximity (gap of 1-3). This assumes that the dataset's chronological ordering reflects actual causal relationships — that if Node A triggers an anomaly 2 entries before Node B, A likely influenced B. This is a reasonable heuristic for tightly-coupled microservice architectures but may produce false edges in systems with independent failure modes.

Identity theft edges, by contrast, represent verified causation — the identity ledger proves that one node is using another's credentials.

## Current System Caps

| Constraint | Limit | Reason |
| :--- | :--- | :--- |
| Node range | IDs 1-499 legitimate, ≥500 flagged as Ghost | Hard-coded boundary in Layer 0 |
| Graph window | Last 200 anomaly events | Deque maxlen in GraphEngine |
| Feature window | Last 50 events per node | Rolling buffer in FeatureEngine |
| Patient Zero window | 60 ticks | Pruning threshold in PatientZeroTracker |
| Database cap | 10,000 rows | Auto-pruning in HistoryDatabase |
| WebSocket clients | ~100 concurrent | Application-layer iteration limit |
| PageRank history | 20 ticks per node | Stability variance calculation window |

## What Would Need to Change for Production

1. **Message Queue:** Replace the synchronous `clients[]` broadcast with a proper pub/sub system (Redis, Kafka).
2. **Distributed Graph Engine:** Move GraphEngine to a dedicated service with persistent state, supporting horizontal scaling.
3. **Adaptive EWMA:** Auto-tune the alpha parameter based on observed traffic patterns rather than using a fixed 0.15.
4. **Extended Windows:** Allow configurable Patient Zero and Graph windows based on the expected attack tempo.
5. **Authentication:** Add proper auth to the WebSocket and REST endpoints (currently open for demonstration).
