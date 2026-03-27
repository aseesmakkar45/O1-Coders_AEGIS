# AEGIS Defense System

**A real-time cyber-forensic attribution platform that reconstructs truth from deceptive telemetry to convict the hidden Shadow Controller orchestrating network attacks.**

---

## 1. The Problem: "Green Dashboards Kill Networks"

Modern distributed networks face a massive vulnerability: attackers don't just break servers—they *lie about breaking them*. When a compromised microservice is exfiltrating data, it doesn't send up a red flag. It broadcasts `{"status": "OPERATIONAL"}` to your SIEM. Standard monitoring tools like Datadog or Splunk implicitly trust the telemetry they ingest. If a compromised node says it's healthy, the dashboard turns green. 

As an engineer, you know that blindly trusting client-side reporting in a zero-trust architecture is a flaw. But when your network goes down, you're faced with thousands of cascaded alerts, and the origin point is usually hidden behind perfectly normal-looking API logs.

## 2. The Challenge: The Shadow Controller

The Round 2 Hackathon Problem drops us right into this scenario:
Find the hidden **Shadow Controller** within legitimate, dense network traffic. 

This isn't a loud botnet throwing DDoS spikes. This is a quiet, sophisticated orchestrator proxying its commands through legitimate nodes, using identity spoofing to blend in. The challenge is mathematically separating *correlation* (nodes dying together) from *causation* (Node A ordered Node B to die), and then isolating the node structurally responsible for the entire attack topology.

## 3. Our Approach: Data-Driven Causal Reconstruction

AEGIS solves this problem entirely without relying on "trusted" signals. We built a 3-stage validation and attribution engine:

### Phase 1: Multi-Layer Truth Reconstruction
Everything starts by distrusting the payload. When an event hits `dataset_reconstructor.py`, it passes through a gauntlet:
*   **Identity Verification:** We decode Base64 hardware tokens embedded in the logs. If a token suddenly shifts to a new IP, we immediately flag **IDENTITY_THEFT** and map a hard dependency line between the victim and the thief.
*   **Contradiction Traps:** The engine correlates HTTP transport codes against internal JSON application states. If the JSON says "OPERATIONAL" but the transport layer drops a 500 or experiences a 4-sigma latency spike, the engine slashes the node's trust score.

### Phase 2: Building the Causal Graph
Instead of just counting errors, we map *who caused what*. 
`graph_engine.py` ingests penalized anomalies into a 200-event sliding window. When anomalies trigger back-to-back chronologically across different servers, the engine structurally links them. This means our graph edges aren't theoretical—they are direct temporal API cascades. 

### Phase 3: Shadow Controller Attribution
Once we have our causal graph, we don't just look for the node with the most errors. We pass the graph through our `attribution_engine.py` which runs a 5-signal consensus:
1.  **Propagation (30%):** Does this node initiate cascades downstream?
2.  **Betweenness Centrality (30%):** Does this node act as the critical bridge for lateral movement across clusters?
3.  **PageRank (15%):** How much absolute downstream influence does this node project across the network?
4.  **ML Anomaly (15%):** Using `IsolationForest` on latency/load variance, does this node exhibit the rigid, automated timing typical of a Command & Control beacon?
5.  **Frequency (10%):** Absolute traffic volume.

Nodes dominating both Propagation and Betweenness get a deterministic tie-breaking boost. We convict the highest-scoring node globally.

## 4. The Result: Actionable Visual Intelligence

AEGIS outputs definitive intelligence, served via our React/WebSocket command dashboard:
- **The #1 Suspect:** Clearly identified as the Shadow Controller, backed by a mathematical confidence gap.
- **Explainable AI:** Human-readable reasoning translated directly from the math (e.g., "Acts as a primary structural bridge for lateral movement").
- **Live Forensic Sweeps:** Deep-dive UI allowing analysts to inspect the trailing 10-minute historical telemetry of any node in the lattice to verify the engine's findings.

---

### Quick Start

AEGIS runs entirely on an asynchronous Python/FastAPI pipeline with zero build steps required for the frontend.

```bash
# 1. Create and activate environment
conda create -n AEGIS python=3.10 -y
conda activate AEGIS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the engine
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Open the Command Center
# Open http://localhost:8000 in Chrome/Edge
```
