import time
from .patient_zero import PatientZeroTracker, AnomalyEvent
from .logger import AlertLogger
import base64

class NodeState:
    def __init__(self, node_id: str, expected_id: str):
        self.node_id = node_id
        self.expected_id = expected_id
        self.current_trust = 100
        
        # Baselines
        self.ewma_latency = 0.05
        self.std_dev = 0.015
        self.last_schema = "v1.0"
        
        # Trackers
        self.last_anomaly_time = 0
        self.schema_swaps_per_min = 0
        self.schema_swap_reset_time = time.time()
        self.recent_timestamps = []

class TruthReconstructor:
    def __init__(self):
        self.nodes = {} # node_id -> NodeState
        self.tracker = PatientZeroTracker()
        self.logger = AlertLogger()
        self.generated_logs = []
        
        # Initialize some expected states based on the registry in generator
        self._init_node("us-east", "us-east-123")
        self._init_node("ap-south", "ap-south-456")
        self._init_node("eu-central", "eu-central-789")
        self._init_node("sa-east", "sa-east-012")

    def _init_node(self, node_id, expected_id):
        self.nodes[node_id] = NodeState(node_id, expected_id)

    def process_telemetry(self, telemetry: dict):
        node_id = telemetry["node_id"]
        if node_id not in self.nodes:
            return None
            
        node = self.nodes[node_id]
        current_time = telemetry["timestamp"]
        penalty = 0
        anomaly_types = []
        
        # 1. Update EWMA
        lat = telemetry["latency"]
        node.ewma_latency = 0.1 * lat + 0.9 * node.ewma_latency
        
        z_score = (lat - node.ewma_latency) / node.std_dev if node.std_dev > 0 else 0
        if z_score > 3:
            penalty += min(40, (z_score - 3) * 5)
            anomaly_types.append("LATENCY_SPIKE")
            
        # 2. Burst Detection (Traffic Spikes)
        node.recent_timestamps.append(current_time)
        node.recent_timestamps = [t for t in node.recent_timestamps if current_time - t < 1.0]
        if len(node.recent_timestamps) > 10: # DDoS threshold
            penalty += 25
            anomaly_types.append("DDOS_TRAFFIC_BURST")

        # 3. Deception Penalty (Ghost Node)
        if telemetry["http_status"] != 200 and telemetry["json_payload"]["status"] == "Operational":
            penalty += 50
            anomaly_types.append("GHOST_NODE_DECEPTION")

        # 4. Schema Volatility
        if current_time - node.schema_swap_reset_time > 60:
            node.schema_swaps_per_min = 0
            node.schema_swap_reset_time = current_time
            
        if telemetry["schema_version"] != node.last_schema:
            node.schema_swaps_per_min += 1
            node.last_schema = telemetry["schema_version"]
            if node.schema_swaps_per_min > 2:
                penalty += 20
                anomaly_types.append("SCHEMA_ROTATION_ATTACK")

        # 5. Identity Masking
        decoded_id = "?"
        try:
            decoded_id = base64.b64decode(telemetry["encoded_header"]).decode("utf-8")
        except:
             decoded_id = "INVALID_B64"
             
        if decoded_id != node.expected_id:
             penalty += 100
             anomaly_types.append("IDENTITY_THEFT")
             # Log to Patient Zero tracker
             self.tracker.log_anomaly(AnomalyEvent(node.node_id, current_time, "IDENTITY_THEFT", 100, decoded_id))
        elif penalty > 0:
             # Log other severe anomalies for Patient Zero heuristics if needed
             self.tracker.log_anomaly(AnomalyEvent(node.node_id, current_time, anomaly_types[0], penalty))

        # Trust Score Decay & Recovery
        if penalty == 0 and (current_time - node.last_anomaly_time) > 10:
            # Recover 2 points per tick if peaceful
            node.current_trust = min(100, node.current_trust + 2)
        elif penalty > 0:
            node.last_anomaly_time = current_time
            node.current_trust = max(0, node.current_trust - penalty)
            
            # Emit logs for the UI
            primary_anomaly = anomaly_types[0] if anomaly_types else "UNKNOWN"
            log = self.logger.emit(node.node_id, primary_anomaly, node.current_trust, "Detected via multi-layer inspection")
            self.generated_logs.append(log)

        # Build output state for this node
        return {
            "node_id": node.node_id,
            "trust_score": node.current_trust,
            "raw_telemetry": telemetry,
            "decoded_identity": decoded_id,
            "anomalies": anomaly_types
        }

    def get_system_state(self, tick_data: list):
        self.generated_logs = []
        processed_nodes = []
        for t in tick_data:
            state = self.process_telemetry(t)
            if state:
                processed_nodes.append(state)
                
        # Resolve patient zero
        current_time = time.time()
        p0_info = self.tracker.resolve_cluster(current_time)
        
        return {
            "nodes": processed_nodes,
            "new_logs": self.generated_logs,
            "patient_zero": p0_info
        }
