import time
import uuid
import random

# Ground Truth Registry
REGISTRY = {
    "us-east": {"expected_id": "us-east-123", "base_latency": 0.04},
    "ap-south": {"expected_id": "ap-south-456", "base_latency": 0.08},
    "eu-central": {"expected_id": "eu-central-789", "base_latency": 0.03},
    "sa-east": {"expected_id": "sa-east-012", "base_latency": 0.12}
}

class TelemetryGenerator:
    def __init__(self):
        self.nodes = list(REGISTRY.keys())
        self.active_attacks = {}  # Store ongoing attacks injected by the dashboard
    
    def generate_baseline(self, node):
        base_lat = REGISTRY[node]["base_latency"]
        latency = base_lat + random.uniform(-0.01, 0.02)
        
        telemetry = {
            "node_id": node,
            "timestamp": time.time(),
            "latency": latency,
            "http_status": 200,
            "schema_version": "v1.0",
            "encoded_header": self._encode_base64(REGISTRY[node]["expected_id"]),
            "json_payload": {"status": "Operational", "metadata": {"cpu": str(random.randint(10, 40)) + "%"}}
        }
        return telemetry

    def _encode_base64(self, text: str) -> str:
        import base64
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")

    def trigger_attack(self, node: str, attack_type: str):
        self.active_attacks[node] = {
            "type": attack_type,
            "start_time": time.time(),
            "duration": 30 # seconds
        }

    def stop_all_attacks(self):
        self.active_attacks.clear()

    def generate_tick(self):
        """Generates one tick of data for all nodes, applying attacks if active"""
        tick_data = []
        current_time = time.time()
        
        for node in self.nodes:
            # Baseline
            data = self.generate_baseline(node)
            
            # Check attacks
            attack = self.active_attacks.get(node)
            if attack:
                if current_time - attack["start_time"] > attack["duration"]:
                    del self.active_attacks[node] # Attack over
                else:
                    data = self._apply_attack(data, attack["type"])
            
            tick_data.append(data)
            
        return tick_data

    def _apply_attack(self, data, attack_type):
        if attack_type == "DDOS":
            data["latency"] = random.uniform(0.6, 1.2)
        elif attack_type == "GHOST_NODE":
            data["http_status"] = 503
            data["json_payload"]["status"] = "Operational" # Deception
        elif attack_type == "SCHEMA_ROTATION":
            data["schema_version"] = random.choice(["v1.1", "v2.0", "v1.0-beta", "v3.1"])
        elif attack_type == "IDENTITY_MASKING":
            # Inject a FOREIGN identity — pick a different node's ID
            current_node = data["node_id"]
            other_nodes = [n for n in REGISTRY if n != current_node]
            stolen_from = random.choice(other_nodes)
            data["encoded_header"] = self._encode_base64(REGISTRY[stolen_from]["expected_id"])
            
        return data
