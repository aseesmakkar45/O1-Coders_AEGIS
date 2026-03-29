# Scalability and Limits

While AEGIS represents a paradigm leap in conceptual detection structures, its current architecture operates under necessary physical engineering boundaries. It is crucial to define exactly where assumptions begin and technical headroom ends.

## Throughput Ceilings

### Ingestion Rates
The engine `DatasetStreamer` runs at an aggressive continuous loop of 1.5 seconds. The specific implementation pushes batches of `6 events` per tick. Over sustained operations, the absolute ceiling for this node-to-batch ratio relies heavily on single-thread memory alignment within Python. Pushing the batch size statically to 600 per 1.5 seconds exceeds calculation loops and would inherently distort real-time forensic visualizations due to rendering bottlenecks in React.

### Connection Limits
WebSockets utilize persistent socket tunnels. Utilizing the `uvicorn.run(app)` asynchronous thread pool provides massive connection potential. 
However, AEGIS enforces a tight operational ceiling on connection pooling. Massive scaling to thousands of concurrent consumers should transition from brute-force iterating: Let the main engine calculate state and publish directly to a Redis Pub/Sub channel, subsequently handled by a fleet of load-balanced WebSocket termination nodes. Currently, AEGIS uses pure application-layer iteration over the `clients[]` array.

## Mathematical Assumptions

### EWMA Decay Models
The latency detection algorithms rely on specific static alpha values inside the EWMA tracking mechanism (`alpha = 0.15`). 
1. The framework intrinsically assumes the ingestion data does not contain catastrophic initial states. Heavy persistent load during initial system boot will skew the baseline matrix entirely for up to 30 intervals before decaying naturally back to truth.

### Bounded Trajectories
1. Active Anomalies. The memory dictionary limits the sliding decay of tracked data directly (`active_anomalies`). The system forcibly clears objects exceeding 60 seconds delta. Sustained, extremely slow attacks occurring across a 48-hour window without triggering density thresholds will not trip the internal `PatientZeroTracker`.

## Current System Caps
- Maximum Supported Nodes in Schema: Tested to integer bounds up to 500.
- Raw Database Max Cap: Hard truncation sequence `DELETE... NOT IN SELECT DESC LIMIT 10000` enforces SQLite limits directly.
- Concurrent Web Clients: Single-Core instance boundary (~100 concurrent sockets).
