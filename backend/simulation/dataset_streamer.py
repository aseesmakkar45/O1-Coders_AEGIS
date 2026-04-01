"""
DatasetStreamer: Replaces TelemetryGenerator.
Reads system_logs.csv, node_registry.csv, schema_config.csv
and streams events sequentially. Zero synthetic data.
"""
import csv
import os
import base64
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

class DatasetStreamer:
    def __init__(self):
        self.logs: List[Dict] = []
        self.registry: Dict[int, Dict] = {}  # node_id -> {user_agent, is_infected, decoded_id}
        self.schema_config: List[Dict] = []
        self.cursor = 0
        self.batch_size = 6  # 6 events per tick (multi-node interleaved mode)
        self.stream_mode = "NORMAL"
        self.saved_cursor = 0
        self.anomaly_count = 0
        self._load_data()

    def _load_data(self):
        # Load node registry
        reg_path = os.path.join(DATA_DIR, "node_registry.csv")
        with open(reg_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nid = int(row["node_uuid"])
                ua = row["user_agent"]
                # Extract Base64 from user_agent string: "AEGIS-Node/2.0 (Linux) <B64>"
                b64_part = ua.split(" ")[-1] if " " in ua else ua
                try:
                    decoded = base64.b64decode(b64_part).decode("utf-8")
                except Exception:
                    decoded = "INVALID"
                self.registry[nid] = {
                    "user_agent": ua,
                    "is_infected": row["is_infected"].strip() == "True",
                    "encoded_id": b64_part,
                    "decoded_id": decoded
                }

        # Load schema config
        sc_path = os.path.join(DATA_DIR, "schema_config.csv")
        with open(sc_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.schema_config.append({
                    "version": int(row["version"]),
                    "time_start": int(row["time_start"]),
                    "active_column": row["active_column"]
                })

        # Load curated system logs
        logs_path = os.path.join(DATA_DIR, "system_logs.csv")
        with open(logs_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                log_id = int(row["log_id"])
                node_id = int(row["node_id"])

                # Determine active schema
                schema_ver = 1
                active_col = "load_val"
                for sc in self.schema_config:
                    if log_id >= sc["time_start"]:
                        schema_ver = sc["version"]
                        active_col = sc["active_column"]

                # Get load value from active column
                raw_load = row.get(active_col, "") or row.get("load_val", "")  # fallback fix
                load_value = float(raw_load) if raw_load else 0.0

                # Get node registry info
                reg = self.registry.get(node_id, {})

                self.logs.append({
                    "log_id": log_id,
                    "node_id": node_id,
                    "json_status": row["json_status"],
                    "http_response_code": int(row["http_response_code"]),
                    "response_time_ms": int(row["response_time_ms"]),
                    "load_value": load_value,
                    "schema_version": f"v{schema_ver}",
                    "active_column": active_col,
                    "encoded_id": reg.get("encoded_id", ""),
                    "decoded_id": reg.get("decoded_id", "UNKNOWN"),
                    "is_infected": reg.get("is_infected", False),
                })

        print(f"[AEGIS] Loaded {len(self.logs)} telemetry events, {len(self.registry)} nodes")

    def get_total_events(self) -> int:
        return len(self.logs)

    def get_batch(self) -> List[Dict]:
        """Get next batch of events from dataset. Loops when exhausted."""
        if self.cursor >= len(self.logs):
            return []  # Stop streaming at 10,000 instead of looping
            
        end = min(self.cursor + self.batch_size, len(self.logs))
        batch = self.logs[self.cursor:end]
        self.cursor = end
        
        # Handle Anomaly Burst Exit
        if hasattr(self, 'stream_mode') and self.stream_mode == "ANOMALY_BURST":
            self.anomaly_count += len(batch)
            if self.anomaly_count >= 5:  # N events
                self.cursor = getattr(self, 'saved_cursor', 0)
                self.stream_mode = "NORMAL"
                self.anomaly_count = 0

        return batch

    def seek(self, position: int):
        """Jump to a specific position in the dataset (permanently changes stream)."""
        self.cursor = max(0, min(position, len(self.logs)))
        self.stream_mode = "NORMAL"

    def get_current_position(self) -> int:
        return self.cursor

    def seek_to_event(self, anomaly_type: str) -> int:
        """Search dataset for specific real anomalies and trigger Anomaly Burst."""
        seen_identities = {}
        pos = -1
        
        # Find first occurrence
        for idx, event in enumerate(self.logs):
            if anomaly_type == "LATENCY_SPIKE":
                if event["response_time_ms"] > 300:
                    pos = max(0, idx - 2)
                    break
                    
            elif anomaly_type == "DECEPTIVE_TELEMETRY":
                if event["json_status"] == "OPERATIONAL" and event["http_response_code"] != 200:
                    pos = max(0, idx - 2)
                    break
                    
            elif anomaly_type == "SCHEMA_ROTATION":
                if idx > 0 and event["schema_version"] != self.logs[idx-1]["schema_version"]:
                    pos = max(0, idx - 3)
                    break
                    
            elif anomaly_type == "IDENTITY_THEFT":
                did = event["decoded_id"]
                nid = event["node_id"]
                if did != "UNKNOWN" and did != "INVALID":
                    if did not in seen_identities:
                        seen_identities[did] = nid
                    elif seen_identities[did] != nid:
                        pos = max(0, idx - 2)
                        break

        if pos >= 0:
            if not hasattr(self, 'stream_mode') or self.stream_mode == "NORMAL":
                self.saved_cursor = self.cursor
            self.stream_mode = "ANOMALY_BURST"
            self.anomaly_count = 0
            self.cursor = pos
            return pos
            
        return -1
