# AEGIS Defense System Overview

AEGIS is a real-time cyber-forensic platform designed to detect and attribute sophisticated network attacks. The system reconstructs the "ground truth" of network events by cross-validating telemetry across multiple layers, identifying the **Shadow Controller** behind cascading failures.

## Core Features

- **Multi-Layer Validation**: Checks telemetry at the HTTP, JSON, Identity, and Schema levels to detect deceptive payloads.
- **Identity Tracking**: Decodes hardware signatures to prevent identity theft and spoofing.
- **Causal Graph Analysis**: Builds a directed graph of anomalies to distinguish between initial victims (Patient Zero) and orchestrators (Shadow Controller).
- **Attribution Engine**: Ranks nodes based on propagation, betweenness centrality, and behavioral anomalies.
- **Real-time Dashboard**: Provides visual insights into network health, attack propagation, and suspect ranking.

## System Components

1. **Dataset Streamer**: Ingests and simulates live network traffic from CSV sources.
2. **Reconstructor**: Processes raw events and assigns trust scores based on validation results.
3. **Graph Engine**: Manages the temporal causal relationship between anomalous events.
4. **Attribution Engine**: Fuses multiple signals to identify the most influential attack nodes.
5. **Persistence Layer**: Logs all forensic events to a localized SQLite database.
