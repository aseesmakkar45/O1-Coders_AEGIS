# AEGIS Threat Classification Criteria

These are the exact rules used by the backend (`dataset_reconstructor.py` and `patient_zero.py`) to classify threats and compute trust scores. Every number here matches the production code.

## 1. Threat Classification (Priority Order)

Events are evaluated in this exact order. The first matching condition becomes the primary anomaly type:

| Threat | Condition | Trust Penalty |
| :--- | :--- | :--- |
| **GHOST_NODE** | `node_id >= 500` | -40 to -50 |
| **IDENTITY_THEFT** | `decoded_id` is valid AND the node that originally registered this identity is different from the current node | -100 |
| **SCHEMA_ROTATION** | `schema_version` differs from this node's last known schema version | -10 to -15 |
| **DDOS_ATTACK** | Z-score > 3.0 AND `load_value > 0.85` | -45 to -60 |
| **LATENCY_SPIKE** | Z-score > 3.0 AND `load_value <= 0.85` | -15 to -25 |

---

## 2. Key Metrics

- **Z-Score:** `(current_latency - ewma_latency) / std_dev` where `ewma = 0.15 × lat + 0.85 × prev_ewma`. Initial `std_dev` is anchored at `30.0`.
- **HTTP Status:** The raw `http_response_code` (200, 206, 429, 500). Does not trigger a penalty on its own, but is used by the frontend for status classification and Sleeper detection.
- **Load:** The raw `load_value` (0.0 to 1.0). Discriminates between LATENCY_SPIKE and DDOS_ATTACK at the 0.85 threshold.
- **Trust Recovery:** If no penalty is applied and the last anomaly was > 3 ticks ago, trust recovers by +2.0/tick, capped at 100.0.

---

## 3. Patient Zero Detection

The `PatientZeroTracker` maintains a sliding window of active anomalies (60-tick expiry).

### Identification
- **Minimum threshold:** At least 2 active anomalies required to form a cluster.
- **Selection:** The node with the oldest anomaly timestamp in the active cluster is declared Patient Zero.
- **Decay:** Below 2 anomalies, confidence drops by -3/tick. At 0, the Patient Zero state clears.

### Confidence Scoring (Max 100)

| Factor | Calculation | Max Score |
| :--- | :--- | :--- |
| **Anomaly Volume** | active_count × 10 | 40 |
| **Identity Theft** | +35 if any IDENTITY_THEFT events in the cluster | 35 |
| **Node Spread** | unique_affected_nodes × 12 | 25 |

### Smoothing
Confidence approaches the target by at most **+8/tick** (rising) or **-2/tick** (falling). This prevents erratic jumps.

### Propagation Edges
When IDENTITY_THEFT is detected, a directed edge is created from the identity owner to the thief node. These edges are included in the Patient Zero's `linked_nodes` list and injected into the GraphEngine with weight 1.2.

---

## 4. Shadow Controller Attribution

The `AttributionEngine` uses a separate 5-signal pipeline to identify the most causally influential malicious node.

### Final Score Formula
```
Score = 0.30 × Propagation
      + 0.30 × Betweenness
      + 0.10 × PageRank
      + 0.10 × ML_Anomaly
      + 0.05 × Frequency
```

Plus stability boost (from PageRank variance) and dominance boost (+0.05 for nodes scoring ≥0.7 in both Propagation and Betweenness).

### Confidence
The confidence of the #1 suspect equals the score gap between the top-ranked and second-ranked nodes, clamped to [0, 1].

### Closeness Centrality
Computed and reported in the signal breakdown for diagnostic visibility, but deliberately excluded from the scoring formula. Proximity to other nodes does not reliably indicate orchestration control.
