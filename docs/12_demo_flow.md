# Demonstration Flow: The AEGIS Narrative

This guide provides a structured, high-impact demonstration script for AEGIS. The narrative follows a "Normalcy → Breach → Attribution → Response" arc, designed to showcase the system's technical depth in under 5 minutes.

---

## 0. Setup & Initialization
1. **Launch Backend:** `cd backend && python main.py` (or use the `run.bat` wrapper).
2. **Access Dashboard:** Open `http://localhost:8000` in a modern browser (Chrome/Edge/Brave recommended).
3. **Reset State:** Opening the dashboard automatically triggers a server-side reset, ensuring the demo starts at $T=0$.
4. **Visuals:** Toggle **Dark Mode** (top-right) for the high-contrast forensic aesthetic.

---

## Phase 1: The Baseline (0:00 - 0:45)
**Goal:** Establish the "Ground Truth" monitoring capability.

- **Action:** Stay on the **Overview** dashboard. Observe the green pulses on the **Forensic Radar Map**.
- **Script:** *"Welcome to AEGIS. We are currently monitoring a simulated network of 100 nodes. Unlike traditional tools that passively accept telemetry, AEGIS is actively reconstructing truth. Every event you see is being cross-validated across four layers: Hardware Identity, Schema Consistency, Transport Integrity, and Application Logic."*
- **Detail:** Point to the **Live Assets** table. *"Notice the 'Decoded Identity' column. AEGIS is extracting cryptographic hardware tokens from raw traffic to ensure that Node A isn't pretending to be Node B."*

---

## Phase 2: Detecting Deception (0:45 - 2:00)
**Goal:** Show AEGIS catching "Sleeper" nodes and lateral movement.

- **Action:** Watch for the header status to flip to **[ UNDER ATTACK ]**. Red/Purple dots will appear on the Radar Map.
- **Script:** *"The attack has begun. Notice several nodes are still sending 'OPERATIONAL' status in their JSON payloads, but AEGIS has flagged them as 'Sleeper' nodes. Why? Because the transport layer is showing high latency and HTTP 429 errors that contradict the application's claim of health."*
- **Highlight:** Point out an **IDENTITY_THEFT** alert. *"Here is a critical catch: Node 45 just tried to use Node 12's hardware token. AEGIS immediately zeroed its trust score and injected a lateral movement edge into our causal graph."*

---

## Phase 3: Shadow Controller Attribution (2:00 - 3:30)
**Goal:** Differentiate between "Patient Zero" (the victim) and "Shadow Controller" (the orchestrator).

- **Action:** Switch to the **Shadow Control** tab. Locate the pulsing red node in the center of the graph.
- **Script:** *"Traditional security stops at 'Patient Zero'—the first node to fail. AEGIS goes deeper. By analyzing a directed causal graph built from temporal proximity and identity theft, we identify the 'Shadow Controller'—the node with the highest structural influence over the attack."*
- **Evidence:** Point to the **Top Suspects** panel. *"Our #1 suspect isn't the loudest node; it's the most connected. Our attribution engine fuses five signals—Propagation, Betweenness, PageRank, ML Anomaly, and Stability—to convict this node with 90%+ confidence."*

---

## Phase 4: Interactive Response (3:30 - 4:15)
**Goal:** Demonstrate the "Kill Switch" and forensic permanence.

- **Action:** Select the Shadow Controller node and click **[ INITIATE KILL SWITCH ]**. 
- **Script:** *"AEGIS allows for real-time impact modeling. By 'killing' the Shadow Controller, we can observe how the attack graph collapses. We've effectively isolated the orchestrator, and you can see the network influence scores recalculating instantly."*
- **Forensics:** Open the **History** modal from the header. *"Finally, every trust shift, every stolen identity, and every raw telemetry packet is persisted in our immutable SQLite ledger. What the analyst sees live is exactly what the forensic investigator finds in the audit trail."*

---

## Phase 5: Conclusion (4:15 - 5:00)
**Script:** *"AEGIS moves defense from reaction to reconstruction. By enforcing hardware identity and mapping causal influence, we don't just see the fire—we find the hand that lit the match. Thank you."*
