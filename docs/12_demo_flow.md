# Demonstration Flow

This guide walks through a structured demonstration of AEGIS for judges, stakeholders, or technical reviewers. The narrative is designed to build from baseline normalcy through attack detection to Shadow Controller conviction — showing the full depth of the system in under 5 minutes.

## Setup

1. Start the backend: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000`
2. Wait for `Application startup complete.` in the terminal.
3. Open one browser tab to `http://localhost:8000`.
4. Opening the tab automatically triggers a server-side reset — the dataset cursor jumps to position 0 and all engine state is wiped, ensuring a clean start every time.
5. Toggle **Dark Mode** via the top-right button for the full command interface aesthetic.

## Phase 1: The Baseline (~30 seconds)

**Goal:** Establish what a healthy network looks like under AEGIS monitoring.

- Start on the **Overview Tab**. The system status shows NOMINAL. Nodes are appearing on the Forensic Radar Map as green dots.
- Point out the live node counter ticking upward as telemetry streams in at 6 events per 1.5-second tick.
- Switch briefly to the **Analytics Tab**. The Trust Deviation chart is entirely green. The Live Intelligence Stream shows orderly `NORMAL` traffic with healthy HTTP 200 responses and low latency.
- Key message: *"This is AEGIS processing legitimate traffic. Every event is being verified across four independent layers — identity, schema, transport, and application. Right now, everything checks out."*

## Phase 2: Attack Detection (~60-90 seconds in)

**Goal:** Show AEGIS catching deceptive telemetry and identity theft in real time.

- Return to the **Overview Tab**. Within the first minute, the dataset's embedded attack sequences will trigger automatically.
- Watch for the system status to flip to **UNDER ATTACK**. The Patient Zero badge will appear in the header with a rising confidence percentage.
- On the Radar Map, compromised nodes appear as red and purple dots. Propagation edges become visible, connecting infected nodes to their sources.
- The attack vector counters start incrementing — IDENTITY_THEFT, LATENCY_SPIKE, SCHEMA_ROTATION.
- Key message: *"An attacker has breached the network. They're sending fake 'OPERATIONAL' payloads to trick standard monitoring tools, but AEGIS caught the HTTP failures underneath. It's also detected identity theft — one node is using stolen credentials from another — and mapped the actual infection path."*

## Phase 3: The Shadow Controller Reveal

**Goal:** Demonstrate that AEGIS goes beyond Patient Zero to find the true orchestrator.

- Click the **Shadow Control** tab in the left navigation.
- The D3 force-directed attack graph will render, showing the causal topology with nodes sized by threat score.
- The **#1 Shadow Controller** node will be highlighted with a pulsing red glow and a "Suspected Command Node" label.
- Draw attention to the **Top Attack Suspects** panel on the right:
  - The #1 suspect has a purple "Shadow Controller" badge.
  - The **"Why This Node?"** callout explains in plain language why this node was convicted.
  - The signal breakdown bars show Propagation, Bridge (Betweenness), and Anomaly scores.
  - The **Engine Reasoning** section provides specific explanations like *"Primary propagation source — 85% of outgoing causal influence"* and *"Acts as a primary structural bridge for lateral movement."*
- Key message: *"Standard tools stop at Patient Zero — the first node to fail. AEGIS deploys a 5-signal attribution engine over a causal graph built from verified temporal sequences and identity theft edges. It identifies the node that is orchestrating the attack, not just the loudest victim."*

## Phase 4: Kill Switch Demonstration (Optional)

**Goal:** Show the interactive threat response capability.

- Click on the #1 suspect node in the attack graph.
- A detail panel appears with an **"INITIATE KILL SWITCH"** button.
- Click it. The node is removed from the graph engine, simulating quarantine.
- Observe how the threat topology reorganizes — remaining suspects shift in ranking, and the "Network Influence Reduced" banner confirms the impact.
- Key message: *"AEGIS doesn't just detect — it lets analysts model the impact of quarantine actions before executing them. Removing the Shadow Controller visibly degrades the attack graph's structure."*

## Phase 5: Forensic Permanence

**Goal:** Prove that the visual findings are backed by hard, queryable data.

- Click the **HISTORY** button in the top header bar. The forensic ledger opens.
- Show the paginated incident log — every event that was flagged on the dashboard exists here with full metadata: exact timestamps, trust before/after deltas, HTTP codes, decoded identity hashes, schema versions, and severity classifications.
- Apply filters (severity: CRITICAL, or node_id of the Shadow Controller) to demonstrate targeted forensic queries.
- Key message: *"Everything we just saw on the live dashboard is permanently recorded in an embedded SQLite database. The visual outbreak and the forensic log are mathematically identical — they come from the same computation path. This data is exportable as CSV for external analysis."*

## Closing Statement

*"AEGIS is not an alert-forwarding mechanism. It's a mathematical truth engine that verifies telemetry integrity, enforces hardware identity, constructs causal attack graphs, and attributes coordinated attacks to their true source — the Shadow Controller — with full explainable reasoning. Everything displayed in the command interface is backed by persistent, auditable forensic data."*
