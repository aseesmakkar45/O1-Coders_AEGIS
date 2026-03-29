from datetime import datetime
from typing import List, Dict

class AlertLogger:
    def __init__(self):
        self.logs = []
        
    def emit(self, node_id: str, anomaly_type: str, trust_score: float, details: str) -> Dict:
        log = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "node_id": node_id,
            "anomaly_type": anomaly_type,
            "trust_score": trust_score,
            "details": details
        }
        self.logs.append(log)
        # Keep only the last 100 logs
        if len(self.logs) > 100:
            self.logs.pop(0)
        return log
