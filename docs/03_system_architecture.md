# System Architecture

The AEGIS Defense System is a robust, event-driven monolith built for scale and exactness. Designed to emulate a zero-trust network environment, the architecture maps raw telemetry inputs through a highly aggressive scrutiny pipeline, storing the results persistently before streaming them to the client interface.

The system is strictly divided into four distinct phases: **Ingestion**, **Processing Engine**, **Persistent Storage**, and **Real-Time Visualization**.

## Architectural Layers

```mermaid
flowchart TD
    A[Dataset] -->|CSV & Node Registries| B(DatasetStreamer)
    B -->|Batched Events (6Hz)| C{DatasetReconstructor}
    
    C -->|Scores, Anomalies, Identity| D[(HistoryDatabase SQLite)]
    C -->|Snapshot State| E[WebSockets Router]
    
    E -->|JSON Payload 1.5s interval| F[React & D3 Frontend]
    D -.->|History Fetch| F
```

### 1. The Ingestion Layer (`DatasetStreamer.py`)
Operating natively without external brokers to reduce latency, the `DatasetStreamer` handles cold-start telemetry ingestion. 
- **Data Binding:** It joins disparate CSV logs (`data.csv`, `node_registry.csv`, `schema_config.csv`) at runtime.
- **Decoding:** Handles real-time Base64 extractions from raw user-agent strings.
- **Batched Exfiltration:** It acts as a generator, outputting chronological data in controlled sets (6 events per 1.5 seconds) to mimic live, volatile network traffic without overwhelming the reconstruction engine.

### 2. The Engine Layer (`DatasetReconstructor.py` & `patient_zero.py`)
This is the core forensic brain of AEGIS. The Reconstructor is a state-machine that maintains memory of every node in the network.
- **Layer 0-4 Analysis:** All incoming telemetry traverses the multi-layer pipeline (Ghost Node, Schema, Latency, Identity, Deception).
- **Trust Scoring:** It recalculates the floating trust score for every node dynamically.
- **Clustering:** It feeds anomalies into the `PatientZeroTracker`, which applies a 60-second sliding window to group isolated anomalies into confident, originating clusters.

### 3. Persistent Storage (`HistoryDatabase.py`)
AEGIS maintains an embedded SQLite storage plane designed to never drop an event.
- **High-Speed Writes:** Leveraging `check_same_thread=False` and `isolation_level=None` for rapid asynchronous writes directly from the reconstructor thread. 
- **Debouncing:** Prevents event flooding by capping recurring identical anomalies down to a tunable debounce window (e.g., max 1 event every 2.0s per node-type).
- **Pruning Strategy:** Self-healing query structures automatically cap the database to the 10,000 most recent events to prevent unbounded disk growth. 

### 4. Real-Time Transport & Visualization (`main.py` & Dashboard)
The system binds the engine state directly to the consumer interface via FastAPI.
- **Asynchronous Broadcasting:** An `asyncio` task runs concurrently alongside FastAPI's web workers, generating the 1.5-second clock tick, querying the Reconstructor, and broadcasting the exact reconstructed system state to all listening WebSocket clients globally.
- **Stateless Read API:** REST endpoints fetch history directly from SQLite for deep-dive investigations, bridging the volatile live socket data with hard persistent logs.
- **Frontend Engine:** React manages the volatile JSON payload states, handing off rendering to high-performance `<canvas>` APIs and D3 visualization trees.

## Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | Python / FastAPI | Unmatched concurrency via `asyncio`, robust networking. |
| **Transport** | WebSockets (ws://) | Persistent connections bypass HTTP overhead for true real-time. |
| **Database** | SQLite3 | Embedded, zero-configuration database ensuring portability and high throughput for single-node logging. |
| **Frontend Framework**| React 18 | Strict state-based re-rendering mapping perfectly to the engine's streaming payload. |
| **Visualization** | D3.js & HTML5 Canvas | Required for high-framerate rendering of thousands of animated orbital data points without DOM blocking. |
| **Styling** | Tailwind CSS | Utility-first design system guaranteeing exact, pixel-perfect layouts. |
