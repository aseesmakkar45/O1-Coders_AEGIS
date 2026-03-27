# System Design: The Problem and The Solution

## 1. What Does AEGIS Actually Do?

AEGIS is an automated cyber-attribution system. It consumes raw server API logs (telemetry), identifies internal contradictions to find compromised nodes, builds a map of how those failures cascaded over time, and runs mathematical algorithms against that map to single out the "Shadow Controller" operating the attack.

## 2. Why Does It Exist? (The Problem)

Standard network monitoring (think Datadog or Prometheus) relies on one fundamental, fatally flawed assumption: **Trust.**

If a server says API traffic is fine, monitoring tools show a green checkmark. But sophisticated attackers don't just hijack servers; they hijack the telemetry reporting tools.
This creates four severe blindspots for Security Operations Centers (SOC):

**A. Deceptive Telemetry:**
The server is actively participating in a botnet, but it's sending `{"status": "OPERATIONAL"}` to your dashboard. Standard tools ignore it because the payload looks clean.
**B. Identity Obfuscation:**
Attackers clone session tokens (Identity Theft) to impersonate clean nodes. Monitoring tools look at the IP, assume it's the valid server, and drop the alert.
**C. Alert Flooding:**
When the attack finally hits critical mass, hundreds of dependent servers crash entirely. The SOC is hit by an impossible wall of alarms, masking who actually started the cascade (Patient Zero).
**D. The Shadow Controller:**
The attacker’s command hub rarely does the dirty work. It whispers small payloads to proxies, who then execute the loud DDoS attacks. Standard platforms ban the loud proxies and completely miss the quiet orchestrator running the show.

## 3. How Does AEGIS Work Internally? (The Solution)

We engineered AEGIS to strip away trust and reconstruct reality solely from mathematical evidence.

### Step 1: The Integrity Engine
We cross-reference every log against its absolute reality. If the JSON payload says "Operational", but the raw TCP transport latency spiked by 400% (tracked via an Exponential Moving Average standard deviation), AEGIS instantly detects the lie. It immediately penalizes the node's internal "Trust Score". If a node's embedded Base64 hardware signature shows up originating from the wrong node, AEGIS logs a confirmed Identity Theft lateral bridge.

### Step 2: The Causal Graph
Instead of just looking at dying nodes, AEGIS connects the dots across time. If Node 43 throws an anomaly, and 200 milliseconds later Node 12 drops offline, AEGIS draws a directed dependency edge pointing `43 -> 12` within a live graph matrix. It proves cascade causality.

### Step 3: Structural Influence Modeling
Once the causal network graph is built, AEGIS feeds it into a specialized `AttributionEngine` running NetworkX. We calculate:
*   **Propagation Out-Degree:** Who started the most fires?
*   **Betweenness Centrality:** Who connects the different network subnets?
*   **PageRank:** Who sits at the very top of the dependency reverse-tree?
*   **Isolation Forest:** Who is matching the specific, rigid timing patterns of a C2 beacon?

The node that dominates these architectural metrics mathematically *must* be the Shadow Controller. 

## 4. How It Translates To The Operator

AEGIS funnels all this advanced computing into a single React-based situational awareness board.
- The SOC analyst no longer stares at a wall of scrolling red text.
- They look at a **Causal Map** showing the infection routing.
- They look at the **Shadow Control** panel, which states: *Node 42 is the Command Server, with 94% confidence, because it is the primary structural bridge for lateral movement.*

AEGIS doesn't just block IPs; it reconstructs truth from deceptive chaos.
