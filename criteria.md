# AEGIS Threat Classification Criteria

These are the strict mathematical rules embedded directly into the AEGIS backend (`dataset_reconstructor.py`) used to grade the integrity of ingested telemetry.

## System Design Philosophy

Why do we use fixed mathematical penalties instead of abstract machine learning models for initial threat classification? 
**Determinism.** When tracking nation-state or highly sophisticated threat actors, SOC engineers need absolute transparency into why an alert fired. Black-box AI at the ingestion layer creates untrustable pipelines. Our reconstruction layer uses rigid, physics-like rules to break anomalies down into causal data, reserving ML (Isolation Forest) purely for downstream behavioral clustering.

---

## 1. Threat Classification Pipeline

The `DatasetReconstructor` processes every log linearly through these rules. The first condition that breaches truth bounds claims the primary anomaly type:

| Threat Vector | Engineering Condition | Base Penalty |
| :--- | :--- | :--- |
| **GHOST_NODE** | `node_id >= 500` (Node exists entirely outside system registry) | -45 |
| **IDENTITY_THEFT** | Emitted hardware token (Base64) maps to a different registered IP | -100 (Maximum) |
| **SCHEMA_ROTATION** | Log structure format suddenly breaks from regional historical consensus | -12 |
| **DDOS_ATTACK** | Latency Z-score > 3.0 **AND** internal memory/CPU `load_value > 0.85` | -50 |
| **LATENCY_SPIKE** | Latency Z-score > 3.0 **AND** internal memory/CPU `load_value <= 0.85` | -20 |

---

## 2. Telemetry Processing Mechanics

- **Rolling Z-Score Evaluation:** `(current_latency - ewma_latency) / std_dev`
  Rather than using static thresholds, we use an Exponentially Weighted Moving Average (`ewma = 0.15 × lat + 0.85 × prev_ewma`). This means the system organically molds itself to the baseline performance of specific nodes, only alerting when a node deviates sharply from *its own* established history.
- **Trust Recovery Protocol:** If a node stays perfectly clean for 3 consecutive simulation ticks, the system permits a +2.0 trust recovery. This reflects network reality: isolated stutters are ignored, continuous attacks drive scores to zero.

---

## 3. Propagation Causality (Patient Zero)

To trace initial compromise, the system maintains a localized 60-tick rolling window to establish a temporal cluster.

1. **Chronological Primacy:** The node featuring the absolute oldest timestamp inside an active anomaly cluster is computationally flagged as Patient Zero.
2. **Deterministic Edge Drawing:** If **IDENTITY_THEFT** fires, a hard directed edge is instantly forged in memory from the legitimate hardware owner to the hijacked proxy node. This edge is passed directly into the Graph Engine to ensure lateral attacker movement isn't guessed—it is mathematically verified.

---

## 4. Shadow Controller Attribution Engine

The primary hackathon objective revolves around identifying the commanding node. `AttributionEngine` compiles the temporal causal edges built during ingestion and runs them against a 4-signal topological matrix.

### The Algorithm:
```math
Command Score = 0.30(Propagation) + 0.30(Betweenness) + 0.15(PageRank) + 0.15(ML_Anomaly) + 0.10(Frequency)
```

- **Propagation (30%):** Simply summing out-degree influence. High volume means it is initiating cascades.
- **Betweenness (30%):** Does the graph topology force lateral movement through this node?
- **PageRank (15%):** Assesses the recursive downstream architectural influence of the node.
- **ML Anomaly (15%):** The exact multi-dimensional vector variance derived via Scikit-Learn's `IsolationForest`. 

### The Dominance Boost
If a node breaks `0.70` in both Propagation and Betweenness, it triggers an engineering dominance boost (+0.05). In topological analysis, dominating both out-degree influence and cross-cluster bridging mathematically defines a Command and Control (C2) jump-box.

### Verdict Output
The engine returns the highest scorer as the Shadow Controller, generating a `confidence` metric derived directly from the numerical gap between Suspect #1 and Suspect #2.
