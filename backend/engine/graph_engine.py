import networkx as nx
from collections import deque

class GraphEngine:
    """
    Builds a causal graph from a sliding window of recent anomaly events.
    Graph is rebuilt from scratch each tick — no stale edges persist.
    """
    def __init__(self):
        # Sliding window: only last 200 anomaly events
        self.event_window = deque(maxlen=200)
        # Identity theft edges: (owner, spoof_node) -> tick
        self.identity_edges = {}

    def record_anomaly_event(self, node_id, log_id):
        """Record an anomaly event into the sliding window."""
        self.event_window.append({
            "node_id": node_id,
            "log_id": log_id
        })

    def record_identity_edge(self, owner, spoof_node, tick):
        """Record a verified identity theft edge."""
        self.identity_edges[(owner, spoof_node)] = tick

    def kill_node(self, node_id):
        node_id_int = int(node_id)
        # Remove from identity edges
        keys_to_delete = [k for k in self.identity_edges if k[0] == node_id_int or k[1] == node_id_int]
        for k in keys_to_delete:
            del self.identity_edges[k]
        # Remove from event window
        self.event_window = deque(
            (ev for ev in self.event_window if ev["node_id"] != node_id_int),
            maxlen=200
        )
        print(f"[DEBUG] GraphEngine: Killed node {node_id_int}")

    def build_normalized_graph(self, current_tick):
        """Rebuild graph from scratch using only the sliding window."""
        G = nx.DiGraph()
        raw_weights = {}

        # 1. Temporal causal edges from sliding window
        window = list(self.event_window)
        for i in range(len(window)):
            ev_a = window[i]
            for j in range(i + 1, len(window)):
                ev_b = window[j]
                gap = ev_b["log_id"] - ev_a["log_id"]
                if gap < 1:
                    continue
                if gap > 3:
                    break  # sorted by log_id via append order
                if ev_a["node_id"] == ev_b["node_id"]:
                    continue
                # Fixed weights by gap
                if gap == 1:
                    weight = 1.0
                elif gap == 2:
                    weight = 0.7
                else:
                    weight = 0.5
                edge = (ev_a["node_id"], ev_b["node_id"])
                raw_weights[edge] = max(raw_weights.get(edge, 0), weight)

        # 2. Identity theft edges
        for (owner, spoof), tick in self.identity_edges.items():
            edge = (owner, spoof)
            raw_weights[edge] = max(raw_weights.get(edge, 0), 1.2)

        if not raw_weights:
            return G

        max_weight = max(raw_weights.values())
        if max_weight == 0:
            max_weight = 1.0

        for (src, tgt), w_raw in raw_weights.items():
            w_norm = w_raw / max_weight
            G.add_edge(src, tgt, weight=w_norm)

        return G
