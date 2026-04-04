import numpy as np
from sklearn.ensemble import IsolationForest
import networkx as nx
import traceback

class AttributionEngine:
    def __init__(self, config):
        self.config = config
        from engine.feature_engine import FeatureEngine
        from engine.graph_engine import GraphEngine
        
        self.feature_engine = FeatureEngine()
        self.graph_engine = GraphEngine(self.config.half_life_seconds)
        self.pr_history = {} # node_id -> [pr1, pr2, ...]

    def record_event(self, node_id, event, current_tick):
        event["tick"] = current_tick
        self.feature_engine.extract_features(node_id, event)

    def record_propagation(self, source, target, current_tick):
        self.graph_engine.record_propagation(source, target, current_tick)
        
    def record_batch(self, events, current_tick):
        self.graph_engine.record_transitions(events, current_tick)
        
    def execute_attribution(self, active_nodes, current_tick):
        G = self.graph_engine.build_normalized_graph(current_tick)
        if len(G) == 0 or len(active_nodes) < 2:
            return {}
            
        # 1. PageRank
        try:
            pr_raw = nx.pagerank(G, alpha=self.config.pr_alpha, weight='weight', max_iter=self.config.pr_max_iter, tol=self.config.pr_tol)
            pr_vals = list(pr_raw.values())
            max_pr = max(pr_vals) if pr_vals else 1.0
            min_pr = min(pr_vals) if pr_vals else 0.0
            pr_norm_dict = {}
            for k, v in pr_raw.items():
                denom = (max_pr - min_pr) if (max_pr - min_pr) != 0 else 1e-6
                pr_norm_dict[k] = (v - min_pr) / denom
        except Exception:
            pr_norm_dict = {}

        # 2. Betweenness
        try:
            G_dist = G.copy()
            for u, v, d in G_dist.edges(data=True):
                w = d.get('weight', 0.1)
                d['distance'] = 1.0 / w if w > 0 else 10.0
            bc_raw = nx.betweenness_centrality(G_dist, weight='distance')
            
            bc_vals = list(bc_raw.values())
            max_bc = max(bc_vals) if bc_vals else 1.0
            min_bc = min(bc_vals) if bc_vals else 0.0
            bc_norm_dict = {}
            for k, v in bc_raw.items():
                denom = (max_bc - min_bc) if (max_bc - min_bc) != 0 else 1e-6
                bc_norm_dict[k] = (v - min_bc) / denom
        except Exception:
            bc_norm_dict = {}
            
        # 3. Behavioral Anomaly
        X = []
        node_order = []
        for n in active_nodes:
            X.append(self.feature_engine.get_x_vector(n))
            node_order.append(n)
            
        anomaly_scores = {}
        if len(X) >= 2: # Need enough for Isolation Forest properly? >0 actually
            try:
                clf = IsolationForest(contamination=0.1, random_state=42)
                X_np = np.array(X)
                clf.fit(X_np)
                raw_scores = clf.decision_function(X_np)
                
                max_score = np.max(raw_scores)
                min_score = np.min(raw_scores)
                denom = (max_score - min_score) if (max_score - min_score) != 0 else 1e-6
                norm_scores = (raw_scores - min_score) / denom
                final_anomaly = 1.0 - norm_scores
                
                for i, n in enumerate(node_order):
                    anomaly_scores[n] = final_anomaly[i]
            except Exception:
                pass
                
        # 4. Frequency Score & Stability
        total_graph_weight = sum(d['weight'] for u, v, d in G.edges(data=True)) or 1.0
        
        results = {}
        for node in G.nodes():
            pr_norm = pr_norm_dict.get(node, 0.0)
            bc_norm = bc_norm_dict.get(node, 0.0)
            iso_score = anomaly_scores.get(node, 0.0)
            
            in_deg = G.in_degree(node, weight='weight')
            out_deg = G.out_degree(node, weight='weight')
            fs = (in_deg + out_deg) / total_graph_weight
            
            # Stability
            if node not in self.pr_history:
                self.pr_history[node] = []
            self.pr_history[node].append(pr_norm)
            if len(self.pr_history[node]) > 20:
                self.pr_history[node].pop(0)

            variance = np.var(self.pr_history[node]) if len(self.pr_history[node]) > 1 else 0.0
            stability = 1.0 / (variance + 1e-6)
            stability_norm = 1.0 - np.exp(-stability * 0.1) 
            
            final_score = (self.config.alpha * pr_norm) + \
                          (self.config.beta * bc_norm) + \
                          (self.config.gamma * iso_score) + \
                          (self.config.delta * fs)
                          
            # Boost
            final_score = min(1.0, final_score * (1.0 + 0.1 * stability_norm))

            reasoning = []
            if pr_norm > 0.6: reasoning.append(f"Dominates ~{int(pr_norm * 100)}% of downstream network influence.")
            elif pr_norm > 0.3: reasoning.append(f"Moderately influences downstream nodes (~{int(pr_norm * 100)}% flow).")
            
            if bc_norm > 0.6: reasoning.append("Acts as a primary structural bridge for lateral movement.")
            
            if iso_score > 0.6: reasoning.append("Highly rigid communication pattern (potential bot/C2 script).")
            
            if stability_norm > 0.8 and pr_norm > 0.4: reasoning.append("Extremely stable temporal signature indicating long-term orchestration.")
            
            if len(reasoning) == 0: reasoning.append("Minor structural traits, low operational confidence.")

            results[int(node)] = {
                "node_id": int(node),
                "final_score": round(float(final_score), 3),
                "breakdown": {
                    "pagerank": round(float(pr_norm), 3),
                    "betweenness": round(float(bc_norm), 3),
                    "anomaly": round(float(iso_score), 3),
                    "frequency": round(float(fs), 3),
                    "stability": round(float(stability_norm), 3)
                },
                "reasoning": reasoning
            }
            
        return results
