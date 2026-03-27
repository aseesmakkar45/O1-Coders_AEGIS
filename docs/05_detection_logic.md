# Deep Dive: Detection and Attribution Logic

This document breaks down the core architecture of how AEGIS technically isolates a command-and-control node out of thousands of conflicting telemetry lines.

## 1. What is the Attribution Engine?

The `AttributionEngine` (found in `backend/engine/attribution_engine.py`) is the computational brain of AEGIS. Its sole purpose is to ingest an array of broken servers, analyze how their failures interact, and logically convict a single node as the master orchestrated threat.

## 2. Why do we need it?

If you just ban the node throwing the most errors, you are banning the victim. The real attacker is usually a hidden node with very low error volume that is gently nudging other servers to crash. To find it, you need to understand the network's mathematical structure, not just its error logs.

## 3. How does it work internally?

AEGIS runs a continuous 1.5-second loop. Each loop executes the following pipeline:

### A. Feature Extraction
The `FeatureEngine` continuously updates a 50-tick rolling memory for every single node. It tracks absolute values (Load, Latency) and calculates mathematical derivatives: 
*   **Inter-Arrival Variance**: Finds automated C2 beacons by spotting unnatural rigidity in response timing.
*   **Transition Entropy**: Identifies nodes that are erratically jumping between operational schema states.

### B. Causal Graph Building
The `GraphEngine` reviews the last 200 anomalies detected in the network. It assumes sequential temporal priority means causality (e.g. Anomaly A happening immediately before Anomaly B implies A caused B). It builds a `NetworkX DiGraph` mapping out exactly how the attack propagated laterally.

### C. The 5-Signal Convolution
AEGIS evaluates the graph using five parallel algorithms and fuses their outputs to rank offenders.

1.  **Propagation Matrix (30% weight):**
    Measures local out-degree causality. Nodes heavily responsible for immediately tipping over neighbors score highly.
2.  **Betweenness Centrality (30% weight):**
    Analyzes the entire topology to find nodes lying on the shortest paths between all other nodes. High betweenness proves the node is acting as a lateral-movement jump box.
3.  **PageRank (15% weight):**
    Flipped to track "reverse-influence." A node gets high PageRank if it successfully dictates the flow of errors through highly connected sub-clusters.
4.  **Behavioral Anomaly / Isolation Forest (15% weight):**
    The derived `X-vector` from our Feature Extraction is pushed through an SKLearn Isolation Forest model. Nodes acting "structurally different" from the herd get heavily penalized.
5.  **Frequency Amplitude (10% weight):**
    Simple summation of total graph activity localized to that server.

## 4. How it connects to the system

Once `execute_attribution()` derives the top suspect, it doesn't just pass a number. It calculates a normalized `confidence score` (the gap between Suspect #1 and #2) and evaluates the strongest weights to generate English `reasoning` strings (e.g., "Primary propagation source — 84% of outgoing influence").

The JSON payload is seamlessly pushed to the WebSocket buffer, where the React dashboard parses it into the **Target Lock** visual panel you see on the screen.
