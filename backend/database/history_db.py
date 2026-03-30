import sqlite3
import os
import time
from datetime import datetime

class HistoryDatabase:
    def __init__(self, db_path="aegis_history.db"):
        self.db_path = db_path
        self._init_db()
        self.last_prune_time = 0

    def get_connection(self):
        # check_same_thread=False is needed for FastAPI async websocket loops
        return sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS INCIDENT_HISTORY (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    trust_before REAL,
                    trust_after REAL,
                    trust_delta REAL,
                    http_status INTEGER,
                    json_status TEXT,
                    schema_version TEXT,
                    decoded_identity TEXT,
                    propagation_source TEXT,
                    batch_id TEXT,
                    latency_ms REAL
                )
            """)
            
            # Indexes for UI queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON INCIDENT_HISTORY(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_node_id ON INCIDENT_HISTORY(node_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomaly ON INCIDENT_HISTORY(anomaly_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_severity ON INCIDENT_HISTORY(severity)")

            try:
                cursor.execute("ALTER TABLE INCIDENT_HISTORY ADD COLUMN log_id INTEGER")
            except:
                pass

    def insert_incident(self, node_id: str, anomaly_type: str, severity: str, 
                        trust_before: float, trust_after: float, 
                        http_status: int = None, json_status: str = None,
                        schema_version: str = None, decoded_identity: str = None,
                        propagation_source: str = None, debounce_window_sec: float = 2.0,
                        latency_ms: float = None, log_id: int = None, batch_id: str = None) -> bool:
        """
        Inserts an anomaly, returning True if inserted or False if debounced.
        Debounce: Blocks identical anomaly_type on node_id within X seconds.
        """
        now_ts = datetime.now()
        trust_delta = trust_after - trust_before

        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Check Debounce Window
            if debounce_window_sec > 0:
                cursor.execute("""
                    SELECT timestamp FROM INCIDENT_HISTORY 
                    WHERE node_id = ? AND anomaly_type = ? 
                    ORDER BY id DESC LIMIT 1
                """, (node_id, anomaly_type))
                last_row = cursor.fetchone()
                if last_row:
                    try:
                        last_ts = datetime.fromisoformat(last_row[0])
                        if (now_ts - last_ts).total_seconds() < debounce_window_sec:
                            return False  # Debounced
                    except:
                        pass
            
            # 2. Insert
            cursor.execute("""
                INSERT INTO INCIDENT_HISTORY (
                    timestamp, node_id, anomaly_type, severity, 
                    trust_before, trust_after, trust_delta,
                    http_status, json_status, schema_version, 
                    decoded_identity, propagation_source, batch_id, latency_ms, log_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_ts.isoformat(), node_id, anomaly_type, severity,
                trust_before, trust_after, trust_delta,
                http_status, json_status, schema_version, 
                decoded_identity, propagation_source, batch_id, latency_ms, log_id
            ))
            
        self._check_prune()
        return True

    def _check_prune(self):
        """Cap storage at 10,000 rows to prevent unstructured growth."""
        now = time.time()
        if now - self.last_prune_time > 60:  # Check at most once per minute
            self.last_prune_time = now
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM INCIDENT_HISTORY")
                count = cursor.fetchone()[0]
                if count > 10000:
                    cursor.execute("""
                        DELETE FROM INCIDENT_HISTORY WHERE id NOT IN (
                            SELECT id FROM INCIDENT_HISTORY ORDER BY id DESC LIMIT 10000
                        )
                    """)

    def query_history(self, limit=50, offset=0, node_id=None, anomaly_type=None, severity=None, date_filter=None, time_chunk=None, since=None):
        query = "SELECT * FROM INCIDENT_HISTORY WHERE 1=1"
        params = []
        if node_id:
            query += " AND node_id = ?"
            params.append(node_id)
        if anomaly_type:
            query += " AND anomaly_type = ?"
            params.append(anomaly_type)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        if date_filter:
            query += " AND substr(timestamp, 1, 10) = ?"
            params.append(date_filter)
        if time_chunk:
            # chunk expects formats like '00-06', '06-12', '12-18', '18-24'
            if time_chunk == '00-06':
                query += " AND cast(substr(timestamp, 12, 2) as integer) >= 0 AND cast(substr(timestamp, 12, 2) as integer) < 6"
            elif time_chunk == '06-12':
                query += " AND cast(substr(timestamp, 12, 2) as integer) >= 6 AND cast(substr(timestamp, 12, 2) as integer) < 12"
            elif time_chunk == '12-18':
                query += " AND cast(substr(timestamp, 12, 2) as integer) >= 12 AND cast(substr(timestamp, 12, 2) as integer) < 18"
            elif time_chunk == '18-24':
                query += " AND cast(substr(timestamp, 12, 2) as integer) >= 18 AND cast(substr(timestamp, 12, 2) as integer) < 24"
            
        query += f" ORDER BY id DESC LIMIT {int(limit)} OFFSET {int(offset)}"
        
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_summary(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM INCIDENT_HISTORY")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as critical FROM INCIDENT_HISTORY WHERE severity = 'CRITICAL'")
            critical = cursor.fetchone()['critical']
            
            cursor.execute("SELECT anomaly_type, COUNT(*) as c FROM INCIDENT_HISTORY GROUP BY anomaly_type ORDER BY c DESC LIMIT 1")
            top_vector_row = cursor.fetchone()
            top_vector = top_vector_row['anomaly_type'] if top_vector_row else "NONE"
            
            return {
                "total_incidents": total,
                "critical_incidents": critical,
                "top_anomaly_vector": top_vector
            }

    def clear_history(self):
        """Wipes the entire history database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM INCIDENT_HISTORY")
