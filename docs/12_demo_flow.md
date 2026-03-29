# Demonstration Flow

The AEGIS Defense System is designed to be demonstrated as a living, volatile environment. To effectively showcase the capabilities of the system to judges, investors, or stakeholders, follow this structured narrative.

## Preparation
1. Ensure the Python FastAPI process (`main.py`) is actively running.
2. Open exactly one browser tab to `http://localhost:8000`. 
3. *Note:* Opening the tab automatically triggers a server-side state reset. The engine wipes its dataset cursor back to `0`, ensuring the demonstration always begins in a clean, nominal state.

## Phase 1: The Baseline
**The Goal: Establish what "normal" looks like.**
- Direct attention to the **Radar Map**. Explain that time is running linearly around the 24-hour radius. Active green dots indicate healthy heartbeats arriving via WebSockets.
- Direct attention to the **Diagnostic Node Heatmap**. The green tiles assure the audience that all systems are functionally perfect. Mention that typical monitoring tools stop at this depth.

## Phase 2: Detecting the Invisible (The Sleeper Cell)
**The Goal: Show AEGIS unmasking deceptive telemetry.**
- Without touching any controls, wait for the engine to hit the first major dataset shift (usually within the first 60 seconds).
- Point to the **Heatmap**. Certain nodes will begin to transition into a pulsating **Purple** hue. 
- Explain: *"These nodes are Sleeper Cells. They are actively sending back JSON payloads reading `{"status": "OPERATIONAL"}` to bypass standard alerting thresholds. However, AEGIS's multi-layered pipeline has caught them failing underlying HTTP checks. Their trust score is dropping, but they aren't critical yet."*

## Phase 3: The Outbreak & Patient Zero
**The Goal: Demonstrate advanced heuristic clustering and identity verification.**
- Use the **Executive Control Panel** at the top of the UI.
- Click the **IDENTITY THEFT** or **LATENCY SPIKE** scenario trigger.
- **The Execution:** This API request (`/api/seek_event/...`) jumps the dataset forward exactly to a mathematically confirmed attack window and initiates an `ANOMALY_BURST`.
- Watch the **Constellation Map** closely. As the burst hits the engine, SVG lines will geometrically draw themselves across nodes.
- Explain: *"An attacker is cloning hardware identities to move laterally across our isolated nodes. Watch the Constellation map track the physical spread in real-time."*
- Quickly observe the **Radar Map**. A massive glowing dash-ring will instantly materialize around a specific radius.
- Explain: *"The system has engaged its 60-second sliding window tracker. It has mathematically isolated the exact origin node responsible for the entire cascade. That dashed orange line is Patient Zero."*

## Phase 4: Forensic Permanence
**The Goal: Show that the visual interface is backed by hard, irrefutable truth.**
- Click the **EXPORT LOGS** control.
- Open the resulting CSV.
- Show the stakeholder that the visual outbreak they just witnessed on the sleek graphs exists perfectly documented in a granular, highly auditable database format. Point out the severe trust drops, the exact Base64 identity hashes, and the specific anomaly classification flags matching exactly what was shown on the dashboard. 

## Conclusion
Conclude the demonstration by emphasizing that AEGIS is not an alert-forwarding mechanism. It is a mathematical truth engine that verifies integrity, establishes hardware identity, and permanently logs the progression of cyber attacks.
