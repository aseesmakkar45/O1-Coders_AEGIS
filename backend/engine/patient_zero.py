from typing import List, Dict

class AnomalyEvent:
    def __init__(self, node: str, timestamp: float, anomaly_type: str, severity: int, decoded_id: str = None):
        self.node = node
        self.timestamp = timestamp
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.decoded_id = decoded_id

class PatientZeroTracker:
    def __init__(self):
        self.active_anomalies: List[AnomalyEvent] = []
        self.graph_edges = []
        self._current_confidence = 0.0  # Smooth confidence state
        self._last_patient_zero = None
    
    def log_anomaly(self, event: AnomalyEvent):
        self.active_anomalies.append(event)
        
    def resolve_cluster(self, current_time: float):
        # Clean old anomalies (60s window)
        self.active_anomalies = [a for a in self.active_anomalies if current_time - a.timestamp < 60]
        
        if len(self.active_anomalies) < 2:
            # Decay confidence when no cluster
            self._current_confidence = max(0, self._current_confidence - 3)
            if self._current_confidence <= 0:
                self._last_patient_zero = None
                return None
            # Return decaying state
            if self._last_patient_zero:
                return {
                    "patient_zero_node": self._last_patient_zero,
                    "confidence": round(self._current_confidence),
                    "linked_nodes": []
                }
            return None
            
        # The origin is strictly the node with the oldest timestamp in the active cluster
        patient_zero_event = min(self.active_anomalies, key=lambda anomaly: anomaly.timestamp)
        patient_zero = patient_zero_event.node
        self._last_patient_zero = patient_zero
        
        # Compute TARGET confidence from evidence
        anomaly_count = len(self.active_anomalies)
        anomaly_count_score = min(40, anomaly_count * 10)
        
        has_cloned_id = any(a.anomaly_type == "IDENTITY_THEFT" for a in self.active_anomalies)
        identity_strength = 35 if has_cloned_id else 0
        
        unique_nodes = len(set(a.node for a in self.active_anomalies))
        spread_score = min(25, unique_nodes * 12)
        
        target_confidence = min(100, anomaly_count_score + identity_strength + spread_score)
        
        # Smooth approach: move current confidence toward target by up to 8 per tick
        if target_confidence > self._current_confidence:
            self._current_confidence = min(target_confidence, self._current_confidence + 8)
        else:
            self._current_confidence = max(target_confidence, self._current_confidence - 2)
        
        linked = list(set([a.node for a in self.active_anomalies if a.node != patient_zero]))
        
        return {
            "patient_zero_node": patient_zero,
            "confidence": round(self._current_confidence),
            "linked_nodes": linked
        }
