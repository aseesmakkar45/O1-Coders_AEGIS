from pydantic import BaseModel, Field
from typing import Optional, Dict

class JsonPayload(BaseModel):
    status: str
    metadata: Optional[Dict[str, str]] = None

class Telemetry(BaseModel):
    node_id: str
    timestamp: float
    latency: float
    http_status: int
    schema_version: str
    encoded_header: str
    json_payload: JsonPayload

class IncidentLog(BaseModel):
    timestamp: str
    node_id: str
    anomaly_type: str
    trust_score: float
    details: str
