# Backend System and Execution Model

The AEGIS backend is a lightweight, strictly typed FastAPI application designed to serve as both the web server and the persistent simulation loop simultaneously.

The objective of the backend architecture is to orchestrate the volatile data plane. It reads static CSVs and converts them into time-series actions, executing exactly as a live network environment would.

## The FastAPI Scaffold (`main.py`)

The entrypoint is an asynchronous FastAPI app configured to run natively inside `uvicorn`.

### Execution Threading
To prevent the streaming data engine from freezing out the web server REST endpoints, AEGIS isolates logic:
1. **Network Thread:** FastAPI and Uvicorn independently manage incoming HTTP GET requests for history filtering and dashboard serving.
2. **WebSocket Keep-Alives:** The `websocket_endpoint` traps upgrades and maintains an active arrays of `clients`.
3. **The Daemon Loop:** During the `@app.on_event("startup")` trigger, a dedicated `asyncio.create_task(simulation_loop())` is spun off. This task yields execution intentionally every 1.5 seconds (`await asyncio.sleep(1.5)`), ensuring it never blocks network traffic while acting as the metronome driving the analytical engine.

## Memory and State Vectoring

The backend avoids heavy database queries for live validation by maintaining a Hot-State memory architecture. 

When the `DatasetReconstructor` is initialized, it opens a `self.nodes = {}` dictionary. 
As the dataset streams IDs through the pipe, the Reconstructor initializes `NodeState` classes into this dictionary. 
These objects hold running properties like:
- `current_trust`
- `ewma_latency`
- `std_dev`
- `original_identity`

Because this is entirely kept in live RAM, the system applies calculations locally in milliseconds. Database usage is strictly reserved for *immutable log storage*, never lookup matching for validation computations. 

## Dataset Navigation and Emulation
Because AEGIS is built around a non-synthetic, hard dataset, it must behave like a DVD player. 
The system defines absolute temporal traversal endpoints:
- `seek(position)`: Forces the global dataset cursor immediately to a static row index. It subsequently issues a `reconstructor.reset()` command, instantly zeroing out the entire RAM cache, ensuring the visual dashboard cleanly shifts timeline without artifacting.
- `seek_event(anomaly_type)`: A sophisticated search function that traverses ahead in the stream until it mathematically isolates a row conforming to the strict heuristic requirements of strings like `LATENCY_SPIKE`. It then triggers `ANOMALY_BURST` mode, jumping the cursor there for immediate forensic inspection.

## Crash Resilience
The entire data flow is enclosed in fault-tolerant array cleanups. If a connected frontend client crashes, drops its network connection, or reloads mid-transmission, the WebSocket handler intercepts the `WebSocketDisconnect` exception, cleanly severing the dead socket from the `clients` registry, preventing blocking cascades on future global broadcasts.
