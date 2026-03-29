# Frontend Dashboard Architecture

The frontend interface for AEGIS is a single-page React-based dashboard, built to visualize thousands of data points at high framerates. The design prioritizes immediate visual storytelling over static numerical grids.

It acts as a passive consumer of the WebSocket pipeline, processing raw JSON system states and transforming them into immersive visual vectors.

## Key UI Components

### 1. The Executive Control Panel (Top Header)
The orchestrator interface. It displays exact dataset timelines, active batch sizes, and the core simulation toggle controls. It also features Scenario Trigger mechanisms, allowing operators to force the injection of specific threat models (like forcing a Schema Rotation or Identity Theft event) directly down the temporal pipeline for live demonstrations.

### 2. The 24-Hour Forensic Radar Map (Core Feature)
The primary temporal tracker. The Radar Map translates linear time into a 24-hour radial clock face.
- **Persistent History Visualization:** It fetches all past incidents from the SQLite database on load and plots them.
- **Current Streaming:** As new events arrive from the WebSocket, they are plotted live at their exact angular timestamp.
- **Z-Axis Rendering:** The rendering engine specifically guarantees that Patient Zero events and Critical Anomalies are sorted to render on top of nominal data dots.
- **Orbital Outlining:** When Patient Zero is isolated, the map draws a pulsing, dashed orbital ring exactly matching the radius parameter of the compromised hardware identifier.
- **Micro-interactions:** A sophisticated `<canvas>` raycasting system detects mouse hovers over specific sub-pixel anomalies, revealing rich data tooltips detailing the exact trust, latency, and HTTP failures of that historical blip.

### 3. The Lateral Movement Constellation Map
A visual graph database map. Instead of timelines, this targets physical topology. 
Nodes are laid out in an active 2D grid. The frontend ingests the `propagation_graph` arrays. When Identity Theft causes lateral traversal across nodes, the constellation map physically draws illuminated SVG vectors linking the origin node to the newly compromised host, tracking the spread of the infection organically.

### 4. The Diagnostic Node Heatmap
The deep-dive grid. 
Provides a tiled overview of up to 45 concurrent nodes. It drops all numerical pretense and focuses entirely on color psychology and pulse animations.
- **Healthy (Green):** Nominal operations.
- **Warning (Orange):** Trust dipping due to latency or schema mismatches.
- **Critical (Red):** Trust completely bottomed out, node inherently compromised.
- **Sleeper (Purple Pulsing):** The engine detects the node is intentionally obfuscating a low-level infection. The UI assigns a specialized breathing CSS animation, cutting through visual noise immediately.

## Performance and Re-rendering Engine
Because the WebSocket blasts state updates every 1.5 seconds containing arrays of hundreds of node metrics, the dashboard is heavily memoized using React's `useMemo` and `useCallback`.
Instead of forcing DOM rerenders for the dense radar map, the system intentionally delegates the heavy particle plotting to an isolated HTML5 `<canvas>`, achieving perfect 60fps frame pacing even during widespread simulated DDoS events that trigger massive dataset cascades.
