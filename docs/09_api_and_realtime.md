# API and Real-time Communication

AEGIS uses a hybrid communication model, using WebSockets for real-time dashboard updates and REST for historical queries.

## WebSocket Protocol

The WebSocket transmits the current state of the network to the React frontend every 1.5 seconds.

### State Payload

- **`nodes`**: A list of current network nodes with their trust scores and identities.
- **`anomalies`**: A list of recently detected anomalous events.
- **`propagation_graph`**: Causal edges between anomaly nodes.
- **`shadow_controller`**: The current top suspect identified by the Attribution Engine.

## REST API Endpoints

- **`GET /api/history`**: Queries the SQLite forensic database with optional filters for node, anomaly type, and timestamp (`since`).
- **`GET /api/system/status`**: Returns the current health of the reconstruction engine.
- **`POST /api/control/quarantine`**: Issues a quarantine command for a specific node ID.

## Data Consistency

The `since` parameter in the `/api/history` endpoint allows the frontend to fetch only the logs generated during the current session, ensuring synchronization between the live stream and historical ledger.
