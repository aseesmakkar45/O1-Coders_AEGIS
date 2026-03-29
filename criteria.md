# AEGIS Threat Classification Criteria

Here are the exact criteria used by the backend (`dataset_reconstructor.py` and `patient_zero.py`) to classify threats.

## 1. Threat Classification Hierarchy

Events are evaluated **in priority order** — the first condition met becomes the primary anomaly type:

| Threat | Condition | Trust Penalty |
|--------|-----------|--------------|
| **GHOST_NODE** | `node_id >= 500` | -40 to -50 |
| **IDENTITY_THEFT** | `decoded_id` is valid AND the initial `node_id` that registered this identity is different from the current `node_id` | -100 |
| **SCHEMA_ROTATION** | `schema_version != node.last_schema` (version abruptly changed since the last known event for this node) | -10 to -15 |
| **DDOS_ATTACK** | Z-score > 3.0 **AND** `load_value > 0.85` | -45 to -60 |
| **LATENCY_SPIKE** | Z-score > 3.0 **AND** `load_value <= 0.85` | -15 to -25 |

---

## 2. Derived Metrics

The following metrics drive the classification and visualization:

*   **Z-Score (Deviation)**: Calculated as `(latency - ewma_latency) / std_dev` where `ewma_latency = 0.15 * lat + 0.85 * prev_ewma`. Note: `std_dev` is currently heavily anchored at `30.0`.
*   **HTTP Error**: The raw `http_response_code` (200, 206, 429). It doesn't trigger a specific penalty on its own but is heavily used by the frontend for status coloring and inferring "Sleeper" states.
*   **Load %**: The raw `load_value`. It serves as the threshold discriminator between a `LATENCY_SPIKE` and a `DDOS_ATTACK` (threshold is 0.85).
*   **Latency**: The raw `response_time_ms`.

### Trust Recovery
If a node experiences NO penalties during a tick AND its last anomaly was more than 3 ticks ago, its trust score recovers by `+2.0`, capped at `100.0`.

---

## 3. Patient Zero Detection Algorithm

The `PatientZeroTracker` maintains a 60-tick window of active anomalies.

### Identification
*   **Minimum Threshold**: At least **2 active anomalies** must be present to identify a cluster.
*   **P0 Selection**: The node associated with the oldest anomaly timestamp in the active cluster is marked as Patient Zero.
*   **Decay**: If the cluster falls below 2 anomalies, the system confidence drops by `-3/tick`. Once confidence hits 0, the Patient Zero state is cleared.

### Confidence Scoring (Max 100)
The confidence score is a sum of three factors, capped at 100:

| Factor | Calculation | Max Score |
|--------|-------------|-----------|
| **Anomaly Volume** | `Active Anomaly Count × 10` | 40 |
| **Identity Theft** | `+35` if any `IDENTITY_THEFT` events exist in the active cluster | 35 |
| **Spread Ratio** | `Unique Affected Nodes × 12` | 25 |

### Confidence Smoothing
To prevent erratic jumps, the confidence score smoothly approaches the target by a maximum of **+8 per tick** (when rising) or **-2 per tick** (when falling).

### Propagation Tracking
When `IDENTITY_THEFT` is detected, the engine creates a directional edge from the original `identity_owner` to the thief node. These edges are aggregated into the `linked_nodes` list for the active Patient Zero.
