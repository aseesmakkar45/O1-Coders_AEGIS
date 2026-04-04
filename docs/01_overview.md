# AEGIS Defense System: Overview

## What AEGIS Does

AEGIS is a real-time cyber-forensic platform that detects, attributes, and visualizes network attacks — specifically designed to find a hidden **Shadow Controller** operating within legitimate traffic.

Most monitoring tools trust the data they receive. If a node sends `{"status": "OPERATIONAL"}`, the dashboard says everything is fine. AEGIS doesn't work that way. It cross-examines every piece of incoming telemetry against multiple independent signals, catches deception instantly, and traces the attack back to its true orchestrator using causal graph analysis and machine learning.

## Core Capabilities

- **Multi-Layer Truth Reconstruction.** Every event passes through a 4-layer verification pipeline — Ghost Node detection, Identity spoofing checks, Schema mutation tracking, and latency/DDoS analysis. Nodes that lie get penalized immediately.

- **Hardware Identity Tracking.** AEGIS decodes Base64 signatures embedded in user-agent strings to establish a cryptographic identity ledger. When Node 44 starts broadcasting the identity that belongs to Node 12, that's IDENTITY_THEFT — a severe trust penalty and a causal edge in the attack graph.

- **Causal Attack Graph.** A sliding-window directed graph of the last 200 anomaly events, rebuilt from scratch every tick. Edges represent verified temporal causation (anomaly sequences within 1-3 log entries) and confirmed identity theft — not co-occurrence or correlation.

- **Shadow Controller Attribution.** A 5-signal scoring engine fusing Propagation Score, Betweenness Centrality, PageRank, Isolation Forest anomaly detection, and Frequency analysis. The node with the highest composite score is convicted as the Shadow Controller, with full explainable reasoning provided to the analyst.

- **Patient Zero Isolation.** A 60-second sliding window clusters cascading anomalies and identifies the earliest offending node with a smoothed confidence score.

- **Persistent Forensic Logging.** Every trust change, anomaly flag, and identity event is permanently recorded in an embedded SQLite database, searchable and exportable as CSV.

- **Immersive Command Interface.** Six dashboard views — Overview, Analytics, Live Assets, Schema Console, Deceptive Map, and Shadow Control — built with React, D3.js, and HTML5 Canvas for real-time visualization of network state and attack attribution.

## The Design Philosophy

Traditional monitoring reacts to failure. When a node dies, an alarm fires. AEGIS takes a fundamentally different approach:

1. **Audit, don't accept.** All telemetry is subjected to multi-layer verification before it reaches the dashboard. The system assumes every node could be lying.

2. **Track causation, not correlation.** The attack graph builds edges only from verified temporal sequences and identity theft — no synthetic co-occurrence links, no infinite memory accumulation.

3. **Attribute the orchestrator.** Finding the first node that fails (Patient Zero) isn't enough. AEGIS uses graph topology, behavioral ML, and temporal stability analysis to find the node *causing* the cascade — the Shadow Controller.

4. **Persist the truth.** Every computed state is mirrored into SQLite, making the live dashboard and historical queries mathematically identical. What the analyst sees live is exactly what they'll find in the forensic export.
