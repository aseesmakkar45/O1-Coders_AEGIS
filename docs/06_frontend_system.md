# Frontend Dashboard Architecture

The AEGIS frontend is a single-page application embedded directly in `index.html`, rendered by the backend via FastAPI's `HTMLResponse`. It uses React 18 (loaded via CDN with Babel transpilation), D3.js for force-directed graph layouts and canvas rendering, Chart.js for drilldown charts, and Tailwind CSS for styling.

The dashboard acts as a passive consumer of the WebSocket stream. Every 1.5 seconds, it receives the full system state — node snapshots, attribution suspects, graph edges, Patient Zero data, and metrics — and distributes it across six distinct views.

## Dashboard Views

### 1. Overview (Default Tab)
The primary operational view. Provides macro-level situational awareness of the network.

- **Header Bar:** Displays system status (NOMINAL / UNDER ATTACK), the identified Patient Zero with confidence percentage, active node count, dataset position, and a real-time system clock.
- **Forensic Radar Map:** A canvas-based polar visualization plotting every telemetry event by time (angular position, full 24-hour sweep) and node ID (radial distance). Events are color-coded: green for normal, amber for warnings, red for critical, purple for sleeper nodes. Patient Zero events receive an orange glow halo. Historical events from the SQLite database are overlaid and periodically refreshed.
- **Lattice Heatmap:** An alternative grid view showing per-node trust timelines as colored bar sequences. Nodes are sorted by worst trust score. Shadow Controller and Patient Zero nodes receive distinct badge overlays.
- **Live Assets Panel:** A sortable table showing real-time node telemetry — JSON status, HTTP response, decoded identity, last anomaly type, and a trust score progress bar.
- **Attack Vector Counters:** Running totals for each anomaly type (Identity Theft, DDoS, Latency Spike, Schema Rotation, Ghost Node).
- **Real-Time Alert Feed:** Chronological log of backend-generated anomaly alerts with severity coloring.

### 2. Analytics Dashboard
Deep-dive charts for trend analysis and historical context.

- **Trust Deviation Over Time:** A horizontally scrolling bar chart mapping trust scores across 200 ticks. Each bar is color-coded (green/yellow/red) based on the minimum trust in that tick. Clicking a bar selects the corresponding node for drilldown.
- **System Latency Trend:** A Chart.js line graph tracking average latency over the last 60 ticks.
- **Anomaly Volume Trend:** An area chart showing the count of anomalies per tick over the last 60 ticks.
- **Live Intelligence Stream:** A granular terminal readout of every processed event — HTTP codes, latencies, load percentages, trust impacts, and timestamps — with anomaly events highlighted.

### 3. Shadow Control Interface
The crown jewel of the dashboard. Focused entirely on Shadow Controller attribution.

- **Attack Graph:** A D3.js force-directed graph showing the causal topology. Node sizes scale with `final_score`. Colors map to threat level (blue < 30%, orange 30-50%, red > 50%). The #1 suspect pulses with a red glow effect. Edges represent causal propagation paths, with thickness proportional to edge weight. Clicking a node highlights its upstream attack path in red.
- **Top Suspects Panel:** Ranked cards for the top 5 suspects, each showing:
  - Node ID and rank badge
  - Confidence label (HIGH/MEDIUM/LOW based on final_score thresholds)
  - Signal breakdown bars: Propagation, Bridge (Betweenness), Anomaly
  - Temporal Stability indicator (5-segment bar)
  - Engine Reasoning: human-readable explanations from the backend
- **"Why This Node?" Callout:** The #1 suspect gets a prominent explanation panel summarizing its dominance.
- **Kill Switch:** Clicking a node and pressing "INITIATE KILL SWITCH" removes it from the graph engine, simulating quarantine. The dashboard shows the modeled reduction in network influence.

### 4. Schema Console
Tracks schema version mutations across all nodes.
- Shows version rotation events, anomaly-flagged mutations, and recovery transitions.
- Burst detection: 3+ red anomalies in a single tick trigger a warning banner.

### 5. Deceptive Multi-Map Sweep
Alternates between the Radar Map and Lattice Heatmap views for multi-perspective analysis.

### 6. Node Drilldown (Modal)
Clicking any node across any view opens a detailed temporal diagnostics panel:
- **4-Chart Stack:** Latency, Deviation (σ), HTTP Errors, and Load (%) over a 10-minute window, rendered via Chart.js.
- **Metadata Summary:** Endpoint path, zone, average latency, standard deviation, anomaly signature, and threat badge.
- Data patterns are dynamically adapted to the node's threat classification (sleeper, malware, suspect, clean).

## Rendering Strategy

The dashboard handles high-frequency updates (every 1.5 seconds) across hundreds of nodes without frame drops through several techniques:

- **React Memoization:** `useMemo` and `useCallback` prevent unnecessary re-renders. Only components whose input data actually changed will re-render.
- **Canvas Rendering:** The Radar Map and its thousands of data points are drawn directly to `<canvas>` via the 2D context API, bypassing DOM overhead entirely.
- **D3 Force Simulation:** The Shadow Control graph runs an isolated D3 physics simulation that updates node positions via `requestAnimationFrame`, independent of React's render cycle.
- **History Windowing:** The WebSocket history buffer is capped at 10 minutes of data. Older ticks are automatically pruned to prevent memory growth.
