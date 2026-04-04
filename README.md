# AEGIS Defense System

**A real-time cyber-forensic attribution platform that reconstructs truth from deceptive telemetry and convicts the hidden Shadow Controller orchestrating network attacks.**

---

## The Problem

Modern distributed networks face a deceptively simple challenge: attackers don't just break things — they *lie about breaking them*. A compromised microservice can broadcast `{"status": "OPERATIONAL"}` to every monitoring dashboard while silently exfiltrating data, rotating database schemas, or spreading laterally through stolen credentials.

Standard monitoring tools — Datadog, Splunk, Prometheus — trust the telemetry they receive. When a node says it's healthy, the dashboard shows green. AEGIS was built because green dashboards kill networks.

## The Challenge

The Round 2 problem demands identifying a hidden **Shadow Controller** buried within legitimate network traffic. This isn't a loud attacker tripping alarms — it's a quiet orchestrator using other nodes as proxies, masking its influence behind layers of normal-looking API interactions. Finding it requires separating *correlation* from *causation*, and *symptoms* from *source*.

## Our Approach

AEGIS solves this in three stages:

1. **Truth Reconstruction.** Every incoming telemetry event passes through a 4-layer verification pipeline that cross-examines HTTP transport codes against JSON application payloads, validates hardware identity via Base64 signature decoding, and detects schema manipulation. When the data lies, AEGIS catches it immediately and penalizes the node's trust score.

2. **Causal Graph Construction.** Rather than correlating which nodes happen to fail at the same time, AEGIS builds a *directed causal graph* from a sliding window of 200 recent anomaly events. Edges are created only when there is strict temporal ordering (anomaly A precedes anomaly B by 1-3 log entries) or verified identity theft (Node X stole Node Y's credentials). The graph is rebuilt from scratch every 1.5 seconds — no stale edges, no accumulated noise.

3. **Shadow Controller Attribution.** A 5-signal scoring engine fuses graph topology with behavioral machine learning to rank every node by its true influence:

| Signal | Weight | What It Measures |
| :--- | :--- | :--- |
| **Propagation** | 30% | How many downstream anomalies this node *causes* |
| **Betweenness Centrality** | 30% | Whether this node acts as the structural bridge for lateral movement |
| **PageRank** | 10% | Downstream orchestration dominance across the full graph |
| **ML Anomaly** | 10% | Rigid, bot-like communication patterns detected by Isolation Forest |
| **Frequency** | 5% | Raw edge activity volume |

Nodes that dominate both Propagation and Betweenness receive a deterministic tie-breaking boost. Temporal stability analysis rewards sustained orchestration over transient spikes.

## The Result

AEGIS produces a ranked list of suspects with the **#1 Shadow Controller** clearly identified, along with:
- A confidence score measuring how distinctly it stands above the next suspect
- Human-readable reasoning explaining *why* the system believes this node is the orchestrator
- A full visual attack graph showing the causal propagation path
- A simulated Kill Switch to model the network impact of quarantining the threat

## Architecture

The system is a FastAPI monolith driven by a 1.5-second async simulation loop.

**Backend:** Python 3.10, FastAPI, NetworkX, scikit-learn (IsolationForest), NumPy, SQLite3
**Frontend:** React 18, D3.js, Chart.js, HTML5 Canvas, Tailwind CSS
**Transport:** WebSocket (real-time) + REST (historical queries)

## Documentation

| Document | Contents |
| :--- | :--- |
| [01_overview.md](docs/01_overview.md) | System capabilities and design philosophy |
| [02_problem_and_solution.md](docs/02_problem_and_solution.md) | The vulnerabilities AEGIS addresses |
| [03_system_architecture.md](docs/03_system_architecture.md) | Layered architecture with Attribution Engine details |
| [04_data_flow.md](docs/04_data_flow.md) | Event lifecycle from CSV ingestion to WebSocket broadcast |
| [05_detection_logic.md](docs/05_detection_logic.md) | Trust scoring, anomaly classification, and attribution formula |
| [06_frontend_system.md](docs/06_frontend_system.md) | Dashboard views and rendering strategy |
| [07_backend_system.md](docs/07_backend_system.md) | Module structure and execution model |
| [08_database_design.md](docs/08_database_design.md) | SQLite schema, debouncing, and pruning |
| [09_api_and_realtime.md](docs/09_api_and_realtime.md) | REST endpoints, attribution APIs, WebSocket payload |
| [10_consistency_model.md](docs/10_consistency_model.md) | How live and historical data stay synchronized |
| [11_scalability_and_limits.md](docs/11_scalability_and_limits.md) | Throughput ceilings and design assumptions |
| [12_demo_flow.md](docs/12_demo_flow.md) | Step-by-step guide for live demonstrations |

## Quick Start

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
# http://localhost:8000
```

**Live Demo:** [https://o1-coders-aegis-i30a.onrender.com](https://o1-coders-aegis-i30a.onrender.com)
