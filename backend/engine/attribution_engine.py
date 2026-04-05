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
        self.graph_engine = GraphEngine()
        self.pr_history = {} # node_id -> [pr1, pr2, ...]

    def record_event(self, node_id, event, current_tick):
        event["tick"] = current_tick
        self.feature_engine.extract_features(node_id, event)

    def record_identity_edge(self, owner, spoof_node, current_tick):
        self.graph_engine.record_identity_edge(owner, spoof_node, current_tick)

    def record_anomaly(self, node_id, log_id):
        self.graph_engine.record_anomaly_event(node_id, log_id)
        
    def execute_attribution(self, active_nodes, current_tick):
        G = self.graph_engine.build_normalized_graph(current_tick)
        if len(G) == 0 or len(active_nodes) < 2:
            return {}

        # --- Helper: safe min-max normalize to [0,1], fallback 0.5 if flat ---
        def _safe_norm(raw_dict):
            if not raw_dict:
                return {}
            vals = list(raw_dict.values())
            mx, mn = max(vals), min(vals)
            if mx == mn:
                return {k: 0.5 for k in raw_dict}
            return {k: (v - mn) / (mx - mn) for k, v in raw_dict.items()}

        # 1. PageRank
        try:
            pr_raw = nx.pagerank(G, alpha=self.config.pr_alpha, weight='weight', max_iter=self.config.pr_max_iter, tol=self.config.pr_tol)
        except Exception:
            pr_raw = {}
        pr_norm_dict = _safe_norm(pr_raw)

        # 2. Betweenness Centrality
        try:
            G_dist = G.copy()
            for u, v, d in G_dist.edges(data=True):
                w = d.get('weight', 0.1)
                d['distance'] = 1.0 / w if w > 0 else 10.0
            bc_raw = nx.betweenness_centrality(G_dist, weight='distance')
        except Exception:
            bc_raw = {}
        bc_norm_dict = _safe_norm(bc_raw)



        # 4. Propagation Score (new signal) — sum of outgoing edge weights per node
        prop_raw = {}
        for node in G.nodes():
            prop_raw[node] = sum(d.get('weight', 0) for _, _, d in G.out_edges(node, data=True))
        prop_norm_dict = _safe_norm(prop_raw)

        # 5. Behavioral Anomaly (Isolation Forest — unchanged)
        X = []
        node_order = []
        for n in active_nodes:
            X.append(self.feature_engine.get_x_vector(n))
            node_order.append(n)
            
        anomaly_scores = {}
        if len(X) >= 2:
            try:
                clf = IsolationForest(contamination=0.1, random_state=42)
                X_np = np.array(X)
                clf.fit(X_np)
                raw_scores = clf.decision_function(X_np)
                
                max_score = np.max(raw_scores)
                min_score = np.min(raw_scores)
                if max_score == min_score:
                    final_anomaly = np.full_like(raw_scores, 0.5)
                else:
                    norm_scores = (raw_scores - min_score) / (max_score - min_score)
                    final_anomaly = 1.0 - norm_scores
                
                for i, n in enumerate(node_order):
                    anomaly_scores[n] = final_anomaly[i]
            except Exception:
                pass
                
        # 6. Frequency Score (unchanged)
        total_graph_weight = sum(d['weight'] for u, v, d in G.edges(data=True)) or 1.0
        
        results = {}
        for node in G.nodes():
            pr_norm = pr_norm_dict.get(node, 0.0)
            bc_norm = bc_norm_dict.get(node, 0.0)
            prop_norm = prop_norm_dict.get(node, 0.0)
            iso_score = anomaly_scores.get(node, 0.0)
            
            in_deg = G.in_degree(node, weight='weight')
            out_deg = G.out_degree(node, weight='weight')
            fs = (in_deg + out_deg) / total_graph_weight
            
            # Stability (unchanged)
            if node not in self.pr_history:
                self.pr_history[node] = []
            self.pr_history[node].append(pr_norm)
            if len(self.pr_history[node]) > 20:
                self.pr_history[node].pop(0)

            variance = np.var(self.pr_history[node]) if len(self.pr_history[node]) > 1 else 0.0
            stability = 1.0 / (variance + 1e-6)
            stability_norm = 1.0 - np.exp(-stability * 0.1) 
            
            # Final 5-signal formula (closeness excluded — proximity ≠ control)
            final_score = (self.config.w_propagation * prop_norm) + \
                          (self.config.beta * bc_norm) + \
                          (self.config.alpha * pr_norm) + \
                          (self.config.gamma * iso_score) + \
                          (self.config.delta * fs)
                          
            # Stability boost (unchanged)
            final_score = min(1.0, final_score * (1.0 + 0.1 * stability_norm))

            # Dominance boost: deterministic tie-breaker for nodes dominant in BOTH
            # primary causal signals (propagation AND betweenness)
            if prop_norm >= 0.7 and bc_norm >= 0.7:
                final_score = min(1.0, final_score + self.config.dominance_boost)

            reasoning = []
            if prop_norm > 0.6: reasoning.append(f"Primary propagation source — {int(prop_norm * 100)}% of outgoing causal influence.")
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
                    "propagation": round(float(prop_norm), 3),
                    "betweenness": round(float(bc_norm), 3),
                    "pagerank": round(float(pr_norm), 3),
                    "anomaly": round(float(iso_score), 3),
                    "frequency": round(float(fs), 3),
                    "stability": round(float(stability_norm), 3)
                },
                "reasoning": reasoning
            }
            
        # Confidence: score gap between #1 and #2 suspect, clamped to [0, 1]
        if len(results) >= 2:
            ranked = sorted(results.values(), key=lambda x: x['final_score'], reverse=True)
            confidence = ranked[0]['final_score'] - ranked[1]['final_score']
            confidence = max(0.0, min(1.0, confidence))
            results[ranked[0]['node_id']]['confidence'] = round(confidence, 3)

        return results

