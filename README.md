# AEGIS Defense System

AEGIS is a startup-grade, real-time cyber-forensic analysis and anomaly detection platform. It is engineered to discard the concept of "trusted telemetry" by employing a mathematical, deterministic pipeline that exposes deceptive node behavior, identity theft, and latent performance cascades across distributed network architectures.

![AEGIS Dashboard Header](https://via.placeholder.com/800x120?text=AEGIS+DEFENSE+SYSTEM)

## The Core Philosophy

Traditional monitoring tools (like Datadog or Splunk) are built to trust the inputs they are given. If a compromised microservice sends an `{"status": "OPERATIONAL"}` payload, the dashboard glows green, even if that service is silently dropping packets or rotating database schemas maliciously. 

**AEGIS assumes nothing.** 

It cross-examines raw transport metrics against application-level JSON payloads. It maps underlying hardware Identity hashes (extracted from Base64 user agents) to establish a strict node registry. When telemetry lies, AEGIS immediately zeroizes the `Trust Score` and flags the **Deceptive Telemetry** attempt, logging the truth to an embedded persistent datastore before broadcasting the state to an immersive, real-time Command Center.

## High-Fidelity Intelligence

AEGIS shifts the security paradigm from *symptom alerting* to *origin attribution*:
- **Unmasking The Sleeper:** The system identifies nodes that are compromised but intentionally keeping their footprint small, rendering them visually distinct as "Sleeper Cells" before they spread.
- **Isolating Patient Zero:** Using a cascading temporal heuristic, AEGIS tracks massive concurrent failure events (like DDoS waves or Identity spread) within a rigorous 60-second sliding window, mathematically drawing a direct vector to the exact node that initiated the sequence.
- **Data Permanence:** The instantaneous dashboard state is perfectly mirrored by a rigorous SQLite backend logging structure, meaning every visual ping maps flawlessly to a row in an exportable historical CSV.

## Architecture

The system operates as a volatile state-machine built inside **Python & FastAPI**, driven by an asynchronous 1.5-second simulation loop. It relies on no external brokers (like Redis or Kafka), handling ingestion, memory-state reconstruction, SQLite writing, and WebSocket broadcasting sequentially on a single core. The frontend is a highly memoized **React & D3.js** interface orchestrating HTML5 Canvas elements for peak 60fps rendering.

## Documentation Suite

The complete architectural reasoning, database schemas, and detection logic mechanics have been thoroughly indexed.

* [01_overview.md](docs/01_overview.md) — Executive summary and capabilities.
* [02_problem_and_solution.md](docs/02_problem_and_solution.md) — The fundamental vulnerabilities AEGIS solves.
* [03_system_architecture.md](docs/03_system_architecture.md) — Layered engineering specifications. 
* [04_data_flow.md](docs/04_data_flow.md) — Pipeline progression from CSV ingestion to WebSocket dispatch.
* [05_detection_logic.md](docs/05_detection_logic.md) — Trust scoring and anomaly deduction heuristic definitions.
* [06_frontend_system.md](docs/06_frontend_system.md) — Dashboard component map and canvas strategies.
* [07_backend_system.md](docs/07_backend_system.md) — NodeState dictionary mapping and API thread logic.
* [08_database_design.md](docs/08_database_design.md) — Embedded SQLite schemas and debounce caps.
* [09_api_and_realtime.md](docs/09_api_and_realtime.md) — Definition of REST routes and pure WebSocket payloads.
* [10_consistency_model.md](docs/10_consistency_model.md) — Achieving zero-lag mathematical persistence.
* [11_scalability_and_limits.md](docs/11_scalability_and_limits.md) — Technical load ceilings and logic windows.
* [12_demo_flow.md](docs/12_demo_flow.md) — A step-by-step guide to showcasing AEGIS's power.

## Deployment

**Live Demo:** [https://o1-coders-aegis-i30a.onrender.com](https://o1-coders-aegis-i30a.onrender.com)

AEGIS is self-contained. 
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the core simulation engine
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Access the Command Center
Navigate to http://localhost:8000/
```
