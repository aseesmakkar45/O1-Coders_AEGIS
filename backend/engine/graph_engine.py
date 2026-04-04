import networkx as nx
import numpy as np

class GraphEngine:
    """
    Builds the graph and applies Exponential Temporal Decay on edges, applying normalization.
    """
    def __init__(self, half_life_seconds):
        self.half_life_seconds = half_life_seconds
        self.lambda_ = np.log(2) / max(self.half_life_seconds, 1)
        self.edges = {} # (src, tgt) -> [tick1, tick2, ...]

    def record_propagation(self, source, target, tick):
        edge = (source, target)
        if edge not in self.edges:
            self.edges[edge] = []
        self.edges[edge].append(tick)
        
    def kill_node(self, node_id):
        node_id_int = int(node_id)
        keys_to_delete = []
        for src, tgt in self.edges.keys():
            if src == node_id_int or tgt == node_id_int:
                keys_to_delete.append((src, tgt))
        for k in keys_to_delete:
            del self.edges[k]
        print(f"[DEBUG] GraphEngine: Killed node {node_id_int}, removed {len(keys_to_delete)} edges")
        
    def record_transitions(self, events, current_tick):
        window_size = 5
        max_time_gap = 30
        for i in range(len(events)):
            for j in range(i + 1, min(i + window_size, len(events))):
                node_a = events[i]["node_id"]
                node_b = events[j]["node_id"]
                
                dt = j - i
                if node_a != node_b and dt <= max_time_gap:
                    self.record_propagation(node_a, node_b, current_tick)
                    
    def build_normalized_graph(self, current_tick):
        G = nx.DiGraph()
        raw_weights = {}
        for edge, ticks in self.edges.items():
            if len(ticks) == 0:
                continue
            # Weight = number of recorded transitions (edges persist forever, graph always grows)
            weight = float(len(ticks))
            raw_weights[edge] = weight
                
        if len(raw_weights) == 0:
            return G

        max_weight = max(raw_weights.values()) if raw_weights else 1.0
        if max_weight == 0: max_weight = 1.0
            
        for (src, tgt), w_raw in raw_weights.items():
            w_norm = w_raw / max_weight
            G.add_edge(src, tgt, weight=w_norm)
                
        return G
