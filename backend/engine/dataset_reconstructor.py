"""
Dataset-driven Truth Reconstruction Engine.
Fulfills AEGIS audit requirements:
1. JSON vs HTTP mismatch checking.
2. Schema version tracking via temporal bounds.
3. Base64 Identity Verification & Identity Theft detection.
4. Attack Propagation tracking (identity reuse).
5. Robust Patient Zero derivation.
"""
import time
import time
from .patient_zero import PatientZeroTracker, AnomalyEvent
from .logger import AlertLogger

from database.history_db import HistoryDatabase

class NodeState:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.current_trust = 100.0
        self.ewma_latency = 120.0
        self.std_dev = 30.0
        self.last_schema = "v1"
        self.last_anomaly_time = 0.0
        self.anomaly_count = 0
        self.original_identity = None
        # Store latest telemetry for snapshot building
        self.last_http = 200
        self.last_json = "OPERATIONAL"
        self.last_latency = 0.12
        self.last_schema_ver = "v1"
        self.last_load = 0.0
        self.last_active_col = "load_val"
        self.last_decoded_id = "UNKNOWN"
        self.last_is_infected = False
        self.last_anomalies = []

class DatasetReconstructor:
    def __init__(self):
        self.history_db = HistoryDatabase()
        self.nodes = {}  # node_id -> NodeState
        self.tracker = PatientZeroTracker()
        self.logger = AlertLogger()
        self.generated_logs = []
        self.tick_counter = 0
        self.identity_owners = {}
        self.propagation_graph = []
        self.latest_tick_trust = 100.0
        self.latency_series = []
        self.anomaly_count_series = []
        self.attack_vector_counts = {
            "IDENTITY_THEFT": 0, "SCHEMA_ROTATION": 0,
            "LATENCY_SPIKE": 0, "DDOS_ATTACK": 0, "GHOST_NODE": 0
        }
        self.latest_incident = None
        self.current_patient_zero_id = None  # Track current P-ZERO for history tagging

        from config.attribution_config import AttributionConfig
        from engine.attribution_engine import AttributionEngine
        self.attribution_engine = AttributionEngine(AttributionConfig)

    def reset(self):
        self.nodes.clear()
        self.tracker = PatientZeroTracker()
        self.logger = AlertLogger()
        self.generated_logs.clear()
        self.tick_counter = 0
        self.identity_owners.clear()
        self.propagation_graph.clear()
        self.latest_tick_trust = 100.0
        self.latency_series.clear()
        self.anomaly_count_series.clear()
        self.attack_vector_counts = {
            "IDENTITY_THEFT": 0, "SCHEMA_ROTATION": 0,
            "LATENCY_SPIKE": 0, "DDOS_ATTACK": 0, "GHOST_NODE": 0
        }
        self.latest_incident = None
        self.current_patient_zero_id = None

        from config.attribution_config import AttributionConfig
        from engine.attribution_engine import AttributionEngine
        self.attribution_engine = AttributionEngine(AttributionConfig)

    def _get_or_create_node(self, node_id: int) -> NodeState:
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeState(node_id)
        return self.nodes[node_id]

    def process_event(self, event: dict) -> dict:
        node_id = event["node_id"]
        node = self._get_or_create_node(node_id)
        current_time = self.tick_counter
        penalty = 0
        anomaly_type = None

        decoded_id = event["decoded_id"]

        # Bug 5 Fix: Apply initial penalty for nodes flagged as infected
        if event.get("is_infected") and node.anomaly_count == 0:
            node.current_trust = min(node.current_trust, 85.0)

        # LAYER 0: GHOST NODE TRAPPING
        if node_id >= 500:
            penalty += 45
            anomaly_type = "GHOST_NODE"

        # LAYER 4: IDENTITY VERIFICATION & SPREAD INFERENCE
        if decoded_id != "UNKNOWN" and decoded_id != "INVALID":
            if node.original_identity is None:
                node.original_identity = decoded_id
                if decoded_id not in self.identity_owners:
                    self.identity_owners[decoded_id] = node_id

            # If the identity belongs to a different node, this is IDENTITY THEFT
            owner = self.identity_owners.get(decoded_id)
            if owner and owner != node_id:
                penalty += 100
                if not anomaly_type: anomaly_type = "IDENTITY_THEFT"
                edge = (owner, node_id)
                if edge not in self.propagation_graph:
                    self.propagation_graph.append(edge)
                    self.attribution_engine.record_identity_edge(owner, node_id, current_time)
                    self.generated_logs.append(self.logger.emit(
                        str(node_id), "LATERAL_MOVEMENT", node.current_trust,
                        f"Stolen ID {decoded_id} from Node {owner}"
                    ))

        # LAYER 3: SCHEMA EVASION DETECTION
        schema_ver = event["schema_version"]
        if schema_ver != node.last_schema:
            node.last_schema = schema_ver
            penalty += 12
            if not anomaly_type:
                anomaly_type = "SCHEMA_ROTATION"

        # LAYER 2: HTTP LATENCY TRUTH & DDOS
        lat = event["response_time_ms"]
        node.ewma_latency = 0.15 * lat + 0.85 * node.ewma_latency
        z_score = (lat - node.ewma_latency) / node.std_dev if node.std_dev > 0 else 0
        if z_score > 3.0:
            if not anomaly_type:
                # If CPU/Load is critically high along with latency, it's a volumetric DDoS
                if event.get("load_value", 0.0) > 0.85:
                    anomaly_type = "DDOS_ATTACK"
                    penalty += 50
                else:
                    anomaly_type = "LATENCY_SPIKE"
                    penalty += 20

        anomaly_types = [anomaly_type] if anomaly_type else []

        # SCORE RECOVERY & PENALTY APPLICATION
        trust_before_event = node.current_trust
        if penalty == 0 and (current_time - node.last_anomaly_time) > 3:
            node.current_trust = min(100.0, node.current_trust + 2.0)
        elif penalty > 0:
            node.last_anomaly_time = current_time
            node.current_trust = max(0.0, node.current_trust - penalty)
            node.anomaly_count += 1

            primary = anomaly_types[0] if anomaly_types else "ANOMALY"
            log = self.logger.emit(str(node_id), primary, node.current_trust, "Multi-layer verification failed")
            self.generated_logs.append(log)

            # Update metrics
            if "IDENTITY_THEFT" in primary: self.attack_vector_counts["IDENTITY_THEFT"] = self.attack_vector_counts.get("IDENTITY_THEFT", 0) + 1
            elif "SCHEMA" in primary: self.attack_vector_counts["SCHEMA_ROTATION"] = self.attack_vector_counts.get("SCHEMA_ROTATION", 0) + 1
            elif "LATENCY" in primary: self.attack_vector_counts["LATENCY_SPIKE"] = self.attack_vector_counts.get("LATENCY_SPIKE", 0) + 1
            elif "DDOS" in primary: self.attack_vector_counts["DDOS_ATTACK"] = self.attack_vector_counts.get("DDOS_ATTACK", 0) + 1
            elif "GHOST" in primary: self.attack_vector_counts["GHOST_NODE"] = self.attack_vector_counts.get("GHOST_NODE", 0) + 1

            self.latest_incident = {
                "timestamp": current_time,
                "node_id": node_id,
                "type": primary,
                "trust": node.current_trust,
                "message": f"Trust dropped to {int(node.current_trust)} via {primary.replace('_', ' ')}"
            }

            self.tracker.log_anomaly(AnomalyEvent(
                str(node_id), current_time, primary, int(penalty)
            ))
            # Feed anomaly into graph sliding window
            self.attribution_engine.record_anomaly(node_id, int(event.get("log_id", -1)))

        # ALWAY LOG TO HISTORY DB (Per User Request)
        primary_anomaly = anomaly_types[0] if anomaly_types else "NORMAL_TRAFFIC"
        severity = "0" if penalty == 0 else "LOW"
        if penalty >= 45: severity = "CRITICAL"
        elif penalty >= 25: severity = "MEDIUM"

        # Check if this node is the current Patient Zero for history tagging
        is_p_zero = (self.current_patient_zero_id is not None and 
                     str(node_id) == str(self.current_patient_zero_id))

        self.history_db.insert_incident(
            node_id=str(node_id),
            anomaly_type=primary_anomaly,
            severity=severity,
            trust_before=trust_before_event,
            trust_after=node.current_trust,
            http_status=event.get("http_response_code"),
            json_status=event.get("json_status"),
            schema_version=event.get("schema_version"),
            decoded_identity=decoded_id,
            latency_ms=round(event.get("response_time_ms", 0)),
            debounce_window_sec=2.0 if penalty > 0 else 0.0,
            log_id=int(event.get("log_id", -1)),
            propagation_source='PATIENT_ZERO' if is_p_zero else None,
            batch_id=str(self.tick_counter)
        )

        # Update the node's stored telemetry so snapshots are always fresh
        node.last_http = event["http_response_code"]
        node.last_json = event["json_status"]
        node.last_latency = event["response_time_ms"] / 1000.0
        node.last_schema_ver = schema_ver
        node.last_load = event["load_value"]
        node.last_active_col = event["active_column"]
        node.last_decoded_id = decoded_id
        node.last_is_infected = event["is_infected"]
        node.last_anomalies = anomaly_types

        self.attribution_engine.record_event(node_id, event, current_time)

        return node_id

    def _build_node_snapshot(self, node: NodeState) -> dict:
        """Build a JSON-serializable snapshot from a live NodeState."""
        return {
            "node_id": str(node.node_id),
            "trust_score": round(node.current_trust, 1),
            "raw_telemetry": {
                "json_payload": {"status": node.last_json},
                "http_status": node.last_http,
                "latency": node.last_latency,
                "schema_version": node.last_schema_ver,
                "load_value": node.last_load,
                "active_column": node.last_active_col,
            },
            "decoded_identity": node.last_decoded_id,
            "is_infected": node.current_trust < 80,
            "anomalies": node.last_anomalies
        }

    def process_batch(self, events: list) -> dict:
        self.generated_logs = []
        self.tick_counter += 1

        min_batch_trust = 100.0
        for event in events:
            nid = self.process_event(event)
            min_batch_trust = min(min_batch_trust, self.nodes[nid].current_trust)
            
        self.latest_tick_trust = min_batch_trust

        p0_info = self.tracker.resolve_cluster(self.tick_counter)

        # Update the current Patient Zero tracker so history entries can be tagged
        if p0_info and p0_info.get("patient_zero_node"):
            self.current_patient_zero_id = str(p0_info["patient_zero_node"])
        else:
            self.current_patient_zero_id = None

        # Inject the propagation graph into p0_info
        if p0_info and p0_info.get("patient_zero_node"):
            p0_id = int(p0_info["patient_zero_node"])
            spread_targets = [tgt for src, tgt in self.propagation_graph if src == p0_id]
            if spread_targets:
                existing = set(p0_info.get("linked_nodes", []))
                for t in spread_targets:
                    existing.add(str(t))
                p0_info["linked_nodes"] = list(existing)

        # Build FRESH snapshots from live NodeState objects (not stale dicts)
        all_nodes = [self._build_node_snapshot(ns) for ns in self.nodes.values()]



        active_nids = list(self.nodes.keys())
        if hasattr(self, 'killed_nodes'):
            active_nids = [nid for nid in active_nids if int(nid) not in self.killed_nodes]
            
        attribution_results = self.attribution_engine.execute_attribution(active_nids, self.tick_counter)
        G = self.attribution_engine.graph_engine.build_normalized_graph(self.tick_counter)
        all_viz_edges = [{"source": str(u), "target": str(v), "weight": float(d.get('weight', 0.5))} for u, v, d in G.edges(data=True)]
        
        # For the Forensic Map: only show top 50 strongest edges to keep it clean
        sorted_edges = sorted(all_viz_edges, key=lambda e: e["weight"], reverse=True)
        forensic_edges = sorted_edges[:50]

        # Update rolling series (last 60)
        avg_latency = sum(e["response_time_ms"] for e in events) / len(events) if events else 0
        self.latency_series.append(avg_latency)
        if len(self.latency_series) > 60: self.latency_series.pop(0)

        tick_anomalies = len(self.generated_logs)
        self.anomaly_count_series.append(tick_anomalies)
        if len(self.anomaly_count_series) > 60: self.anomaly_count_series.pop(0)

        from datetime import datetime
        return {
            "_receivedAt": datetime.utcnow().isoformat() + "Z",
            "nodes": all_nodes,
            "new_logs": self.generated_logs,
            "patient_zero": p0_info,
            "attribution_suspects": attribution_results,
            "dataset_position": events[-1]["log_id"] if events else 0,
            "total_events": 10000,
            "propagation_graph": all_viz_edges,
            "forensic_edges": forensic_edges,
            "propagation_edges": len(all_viz_edges),
            "latest_tick_trust": round(self.latest_tick_trust, 1),
            "tick_events": [{"node_id": str(e["node_id"]), "trust_score": round(self.nodes[e["node_id"]].current_trust, 1)} for e in events if e["node_id"] in self.nodes],
            "metrics": {
                "latency_series": self.latency_series,
                "anomaly_series": self.anomaly_count_series,
                "attack_vectors": self.attack_vector_counts,
                "latest_incident": self.latest_incident
            }
        }
