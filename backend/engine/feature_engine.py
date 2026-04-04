import numpy as np

class FeatureEngine:
    """
    Computes the X vector per node: [Avg Latency, Load, Error Rate, Inter-Arrival Variance, Transition Entropy].
    """
    def __init__(self):
        self.node_histories = {}

    def extract_features(self, node_id, event):
        if node_id not in self.node_histories:
            self.node_histories[node_id] = {
                "latencies": [],
                "loads": [],
                "http_statuses": [],
                "tick_times": []
            }
        
        hist = self.node_histories[node_id]
        hist["latencies"].append(event.get("response_time_ms", 0.0))
        hist["loads"].append(event.get("load_value", 0.0))
        hist["http_statuses"].append(event.get("http_response_code", 200))
        hist["tick_times"].append(event.get("tick", 0.0))
        
        if len(hist["latencies"]) > 50:
            hist["latencies"].pop(0)
            hist["loads"].pop(0)
            hist["http_statuses"].pop(0)
            hist["tick_times"].pop(0)

    def get_x_vector(self, node_id):
        hist = self.node_histories.get(node_id)
        if not hist or not hist["latencies"]:
            return [0.0, 0.0, 0.0, 0.0, 0.0]

        avg_lat = np.mean(hist["latencies"])
        avg_load = np.mean(hist["loads"])
        
        errors = sum(1 for status in hist["http_statuses"] if status != 200)
        error_rate = errors / len(hist["http_statuses"])
        
        diffs = np.diff(hist["tick_times"])
        inter_arrival_variance = np.var(diffs) if len(diffs) > 0 else 0.0
        
        statuses = hist["http_statuses"]
        if len(statuses) < 2:
            transition_entropy = 0.0
        else:
            transitions = {}
            for i in range(len(statuses) - 1):
                t = (statuses[i], statuses[i+1])
                transitions[t] = transitions.get(t, 0) + 1
            total_t = sum(transitions.values())
            transition_entropy = sum(
                - (count/total_t) * np.log2(count/total_t)
                for count in transitions.values()
            )
            
        return [avg_lat, avg_load, error_rate, inter_arrival_variance, transition_entropy]
