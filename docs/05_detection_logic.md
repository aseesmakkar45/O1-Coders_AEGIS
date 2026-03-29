# Detection Logic and Threat Mechanics

AEGIS utilizes deterministic layers of rules and heuristics to classify anomalies. The core philosophy is **layered verification**: a node's reported status is never taken at face value. 

This document details exactly how penalties are derived, scored, and escalated.

## Trust Score Mechanics

Every node possesses an internal continuous `Trust Score`, floating between `0.0` and `100.0`. 
When a node passes all heuristics cleanly for a sustained window (> 3.0 seconds), its trust recovers organically at a rate of `+2.0` per tick. 
When heuristic layers identify breaches, immediate subtractive penalties are applied. 

| Anomaly Type | Trust Penalty | Severity Rating | Description |
| :--- | :--- | :--- | :--- |
| **IDENTITY_THEFT** | `-100` | **CRITICAL** | A hardware identity hash is broadcasting from an illegitimate node ID. |
| **DDOS_ATTACK** | `-45 to -60` | **CRITICAL** | Massive latency spikes overlapping critically high system load volumes. |
| **GHOST_NODE** | `-40 to -50` | **CRITICAL** | Transmission emanating from node IDs strictly outside the allowed registry parameters (> 500). |
| **LATENCY_SPIKE** | `-15 to -25` | **MEDIUM** | Network deterioration exceeding 3-Sigma standard deviation norms. |
| **SCHEMA_ROTATION**| `-10 to -15` | **MEDIUM** | The data schema shape unexpectedly shifted without orchestration. |

## Explaining The Layers

### 1. Identity Spoofing & Lateral Movement
The most aggressive check in AEGIS (Layer 4). 
Every payload contains a Base64 encoded identifier embedded inside the User-Agent. AEGIS decodes this upon ingestion. The `DatasetReconstructor` maintains a permanent ledger mapping `decoded_id -> node_id`. If a known Base64 identity suddenly broadcasts from a different `node_id`, it proves an attacker has moved horizontally across the microservices.
**Action:** The new node's trust is instantly zeroed out. The system documents the physical traversal path (`source -> target`) for the incident API.

### 2. Deceptive Telemetry Trapping
Attackers hide failures by rigging the standard health checks to return nominal values.
AEGIS constantly compares the application layer to the transport layer. If a node sends a `{"status": "OPERATIONAL"}` packet but the raw socket recorded an HTTP 500 network response, AEGIS detects the mask. It instantly labels the event as anomalous and registers the node as compromised.

### 3. Exponential Response Time Validation
AEGIS tracks latency dynamically, eliminating the need for hardcoded thresholds that become brittle under heavy traffic.
The engine calculates an **Exponentially Weighted Moving Average (EWMA)** for every individual node:
`ewma = (0.15 * current_ping) + (0.85 * ewma)`
If a ping exceeds a $Z-Score > 3.0$ standard deviations above its personal norm, the mathematical anomaly is flagged. It is then correlated against CPU `load_val`. High load upgrades the threat to an L7 DDoS.

### 4. Sleeper Cell Identification
A "Sleeper Cell" is a node that is infected but deliberately keeping its footprint small to avoid tripping the trust zeroing thresholds.
The AEGIS UI Engine evaluates the continuous trust score combined with active metrics. If a node is behaving erratically but hovering at a warning state (Trust < 80 but > 30) while reporting deceptive telemetry, the Temporal Heatmaps explicitly paint it in **Purple Infection Hues**, warning analysts of impending lateral expansion.

### 5. Patient Zero Synthesis
If attacks cascade, alerts become useless noise. The `PatientZeroTracker` fixes this by digesting all anomalies continuously.
1. It looks at all active alerts generated inside a `60-second` sliding window.
2. It sorts them strictly by temporal origin.
3. The Absolute Oldest node in an active cascading cluster is declared **Patient Zero**.
4. The system calculates a confidence score based on cluster density, uniqueness, and the presence of cloned identities. 
