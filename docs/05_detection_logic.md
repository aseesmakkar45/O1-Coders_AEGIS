# Detection Logic and Threat Mechanics

AEGIS uses deterministic rule-based layers to classify anomalies and a graph-based machine learning pipeline to attribute the root cause. This document explains exactly how trust penalties are computed, how anomalies are classified, and how the Shadow Controller is mathematically convicted.

## Trust Score Mechanics

Every node maintains a continuous trust score between `0.0` and `100.0`, starting at `100.0`.

**Penalty application:** When a verification layer detects a breach, the corresponding penalty is subtracted immediately. Multiple layers can trigger on the same event, but only the first matching anomaly type is recorded (priority order below).

**Trust recovery:** If a node passes all layers cleanly for a given tick AND its last anomaly was more than 3 ticks ago, it recovers +2.0 per tick, capped at 100.0. This prevents permanent false-positive damage while ensuring genuinely compromised nodes stay flagged.

### Anomaly Classification (Priority Order)

Events are evaluated in this exact order. The first condition met becomes the primary anomaly type:

| Anomaly Type | Penalty | Trigger Condition |
| :--- | :--- | :--- |
| **GHOST_NODE** | -40 to -50 | `node_id >= 500` — transmission from outside the registered node range |
| **IDENTITY_THEFT** | -100 | The decoded Base64 identity was first registered by a different node — proves lateral movement |
| **SCHEMA_ROTATION** | -10 to -15 | The schema version changed since this node's last event — potential evasion tactic |
| **DDOS_ATTACK** | -45 to -60 | Latency Z-score > 3.0 AND system load > 85% — volumetric attack signature |
| **LATENCY_SPIKE** | -15 to -25 | Latency Z-score > 3.0 AND system load ≤ 85% — network degradation without volumetric cause |

### Severity Classification

Severity labels are assigned for database logging based on raw penalty magnitude:
- **CRITICAL:** penalty ≥ 45 (IDENTITY_THEFT, DDOS_ATTACK, GHOST_NODE)
- **MEDIUM:** penalty ≥ 25
- **LOW:** penalty > 0
- **NORMAL_TRAFFIC:** penalty = 0

## The Verification Layers

### Layer 0: Ghost Node Trapping
The simplest check. If a `node_id` is 500 or above, it falls outside the legitimate node registry. These are phantom transmissions — either from an attacker probing the network boundaries or a misconfigured service broadcasting on unauthorized channels.

### Layer 1: Identity Verification and Lateral Movement
The most aggressive check. Every telemetry payload contains a Base64-encoded identity string extracted from the user-agent during ingestion. The Reconstructor maintains a permanent ledger: `{decoded_id → first_seen_node_id}`.

When a decoded identity is seen on a node that doesn't match the ledger entry, AEGIS concludes the identity was stolen. This is the strongest signal of lateral movement — an attacker has compromised one node and is using its credentials to operate from another.

**What happens:**
- The spoofing node receives a -100 trust penalty (instant zero-out).
- A directed edge `(owner → thief)` is recorded in the GraphEngine with weight 1.2 (the highest possible edge weight).
- The edge is permanent — it persists across sliding window rebuilds because identity theft edges are stored separately from temporal events.

### Layer 2: Schema Evasion Detection
Schema versions should change predictably and uniformly across a network. When a single node's schema version suddenly differs from its own previous heartbeat, it suggests the node is being manipulated to evade detection systems that rely on consistent data structures.

The penalty is moderate (-10 to -15) because schema changes can occasionally be legitimate, but repeated rotations compound rapidly.

### Layer 3: Latency and DDoS Detection
AEGIS tracks latency dynamically, avoiding brittle hardcoded thresholds. For each node, it maintains an Exponentially Weighted Moving Average:

```
ewma = 0.15 × current_latency + 0.85 × previous_ewma
```

When the current latency's Z-score exceeds 3.0 standard deviations above the node's personal baseline, the anomaly is flagged. The system then checks `load_value` to distinguish between:
- **DDOS_ATTACK** (load > 85%): The node is being overwhelmed by traffic volume.
- **LATENCY_SPIKE** (load ≤ 85%): The node is degrading without a volumetric cause — potentially performing unauthorized computation.

## Patient Zero Detection

The `PatientZeroTracker` identifies the origin of cascading failures by clustering anomalies temporally.

**Mechanism:**
1. All anomalies are maintained in a 60-tick sliding window.
2. If fewer than 2 anomalies are active, confidence decays by -3/tick. At 0, Patient Zero state clears.
3. When ≥ 2 anomalies are active, the node with the oldest timestamp in the cluster is declared Patient Zero.

**Confidence Scoring (max 100):**

| Factor | Calculation | Max |
| :--- | :--- | :--- |
| Anomaly Volume | active_count × 10 | 40 |
| Identity Theft Presence | +35 if any IDENTITY_THEFT in cluster | 35 |
| Node Spread | unique_affected_nodes × 12 | 25 |

Confidence smooths toward the target by at most +8/tick (rising) or -2/tick (falling), preventing erratic jumps that would confuse analysts.

---

## Shadow Controller Attribution

Patient Zero tells you *where the fire started*. The Shadow Controller engine tells you *who lit the match*.

### Graph Construction
The `GraphEngine` maintains a deque of the last 200 anomaly events. Every tick, it rebuilds a directed `nx.DiGraph` from scratch:

**Temporal causal edges:** If Node A triggered an anomaly at `log_id = T` and Node B triggered an anomaly at `log_id ∈ [T+1, T+3]`, an edge `A → B` is created. Weights decrease with distance:
- Gap of 1: weight 1.0 (strongest causation)
- Gap of 2: weight 0.7
- Gap of 3: weight 0.5

**Identity theft edges:** When identity spoofing is detected, an edge `owner → thief` is injected with weight 1.2 — the highest possible. These edges persist as long as the identity theft record exists.

**What's NOT in the graph:** No co-occurrence edges (nodes failing at the same time don't get connected). No infinite accumulation (the 200-event window naturally drops old data). The graph represents only verified causal relationships.

### Behavioral Fingerprinting
The `FeatureEngine` computes a 5-dimensional vector per node from a rolling window of 50 events:

1. **Average Latency** — Mean response time.
2. **Average System Load** — Mean CPU/system load.
3. **Error Rate** — Fraction of non-200 HTTP responses.
4. **Inter-Arrival Variance** — Variance in time gaps between events. Low variance = bot-like precision.
5. **Transition Entropy** — Shannon entropy of HTTP status code transitions. Low entropy = scripted communication loops.

These vectors are fed into an **Isolation Forest** (contamination = 10%) for unsupervised anomaly detection. The output is inverted and normalized to [0, 1] — high scores indicate rigid, bot-like behavior consistent with C2 scripts.

### The 5-Signal Attribution Formula

```
Score = 0.30 × Propagation
      + 0.30 × Betweenness
      + 0.10 × PageRank
      + 0.10 × ML_Anomaly
      + 0.05 × Frequency
```

All five signals are independently normalized to [0, 1] using safe min-max scaling. If all nodes have identical scores for a signal, everyone gets 0.5 (preventing division-by-zero artifacts).

**Why closeness centrality is excluded:** Closeness measures how *close* a node is to all other nodes in the graph. While it's computed and reported in the breakdown for diagnostic purposes, proximity to the attack surface doesn't reliably indicate control. A node can be close to everything without causing anything. The formula deliberately favors signals that measure *outgoing influence* (Propagation) and *structural control* (Betweenness).

### Stability Boost
Shadow Controllers maintain persistent influence — they don't spike once and disappear. The engine tracks each node's PageRank over a 20-tick sliding window and computes variance:

```
stability = 1 / (variance + ε)
stability_norm = 1 − e^(−stability × 0.1)
final_score = score × (1 + 0.1 × stability_norm)
```

This rewards nodes with consistently high PageRank over time, penalizing transient anomaly bursts.

### Dominance Boost
If a node scores ≥ 0.7 in *both* Propagation and Betweenness, it receives a +0.05 tie-breaking bonus. This ensures the most structurally dominant node is definitively separated from close runners-up.

### Confidence Metric
The confidence of the #1 suspect is computed as the score gap between the top-ranked and second-ranked nodes, clamped to [0, 1]. A high confidence means the Shadow Controller stands clearly above the rest. A low confidence means multiple nodes share similar influence — the attribution is less certain.

### Explainable Reasoning
Each suspect receives a dynamically generated array of human-readable reasoning strings based on their signal scores. Examples:
- "Primary propagation source — 85% of outgoing causal influence."
- "Acts as a primary structural bridge for lateral movement."
- "Highly rigid communication pattern (potential bot/C2 script)."
- "Extremely stable temporal signature indicating long-term orchestration."
