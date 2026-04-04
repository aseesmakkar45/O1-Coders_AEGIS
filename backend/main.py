"""
Purpose: Core entry point for the AEGIS FastApi application.
Inputs: N/A (Starts up server, connects Websockets, handles HTTP)
Outputs: Hosts the API and serves the dashboard UI.
Logic Summary: Instantiates the DatasetStreamer and DatasetReconstructor engines, starts the 5-second asynchronous simulation loop, and binds the REST and WebSocket endpoints for data streaming.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from simulation.dataset_streamer import DatasetStreamer
from engine.dataset_reconstructor import DatasetReconstructor
import asyncio
import os
import traceback

app = FastAPI(title="AEGIS Master Backend — Dataset Driven")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

streamer = DatasetStreamer()
reconstructor = DatasetReconstructor()
clients = []
is_paused = False
loop_status = {"running": False, "ticks": 0, "last_error": None, "last_tick_time": None, "clients_count": 0}

@app.get("/")
def read_root():
    """
    Purpose: Serves the monolithic frontend dashboard.
    Inputs: HTTP GET request to root index.
    Outputs: Raw HTML string rendered by browser.
    Logic Summary: Securely resolves absolute path to frontend/index.html and reads raw contents, falling back to JSON error dictionary on OS failure.
    """
    try:
        html_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return {"status": "AEGIS Core Online", "error": str(e)}

@app.post("/api/seek/{position}")
def seek_dataset(position: int):
    """
    Purpose: Temporal navigation across telemetry.
    Inputs: Integer representing cursor position.
    Outputs: JSON confirmation of state jump.
    Logic Summary: Mutates the internal dataset_streamer cursor state to standard `position` and wipes the Reconstruction engine state vectors for a clean resume.
    """
    streamer.seek(position)
    reconstructor.reset()  # Reset engine state completely
    return {"status": "success", "position": position}

@app.post("/api/seek_event/{anomaly_type}")
def seek_event(anomaly_type: str):
    """
    Purpose: Scenario triggering tool for demonstration.
    Inputs: String representation of Anomaly class (e.g. LATENCY_SPIKE)
    Outputs: Evaluated Cursor target index or an error status object.
    Logic Summary: Linearly jumps the dataset timeline directly to the next index containing the requested event flag.
    """
    pos = streamer.seek_to_event(anomaly_type)
    if pos >= 0:
        return {"status": "success", "event": anomaly_type, "position": pos}
    return {"status": "error", "message": "No matching scenario found"}

@app.get("/api/dataset/info")
def dataset_info():
    """
    Purpose: Diagnostic check for telemetry stream synchronicity.
    Inputs: None.
    Outputs: Dict holding global statistics (total_events, position, state parameters).
    Logic Summary: Maps engine class attributes to JSON output.
    """
    return {
        "total_events": streamer.get_total_events(),
        "current_position": streamer.get_current_position(),
        "batch_size": streamer.batch_size,
        "is_paused": is_paused
    }

@app.post("/api/toggle_pause")
def toggle_pause():
    """
    Purpose: Runtime simulation interruption control.
    Inputs: None.
    Outputs: The toggled boolean flag `is_paused`.
    Logic Summary: Flips the global pause register stopping the `simulation_loop` batch processor execution.
    """
    global is_paused
    is_paused = not is_paused
    return {"status": "success", "is_paused": is_paused}

@app.get("/api/history")
def get_incident_history(limit: int = 50, offset: int = 0, node_id: str = None, anomaly_type: str = None, severity: str = None, date_filter: str = None, time_chunk: str = None):
    """
    Purpose: Retrieve paginated forensic logs.
    Inputs: limit, offset, and optional filter queries (node_id, anomaly_type, severity, date, time).
    Outputs: JSON response encapsulating matched rows.
    Logic Summary: Wraps the SQLite query invocation on the reconstructor history database instance.
    """
    rows = reconstructor.history_db.query_history(limit=limit, offset=offset, node_id=node_id, anomaly_type=anomaly_type, severity=severity, date_filter=date_filter, time_chunk=time_chunk)
    return {"status": "success", "data": rows}

@app.get("/api/history/summary")
def get_history_summary():
    """
    Purpose: Fetch universal stats for executive dashboard metrics.
    Inputs: None.
    Outputs: JSON structure containing volume, severity counts, and primary vectors.
    Logic Summary: Pulls global aggregation counters natively calculated at the DB level.
    """
    summary = reconstructor.history_db.get_summary()
    return {"status": "success", "data": summary}

@app.get("/api/history/node/{node_id}")
def get_node_history(node_id: str, limit: int = 50):
    """
    Purpose: Isolate deep forensics for targeted node analysis.
    Inputs: Target node identifier (`node_id`).
    Outputs: JSON array mapped to chronological events.
    Logic Summary: Fires query_history applying explicit bounding to a single node.
    """
    rows = reconstructor.history_db.query_history(limit=limit, offset=0, node_id=node_id)
    return {"status": "success", "data": rows}

@app.delete("/api/history/clear")
def clear_history():
    """
    Purpose: Wipes the entire history database.
    Inputs: None.
    Outputs: JSON confirmation.
    Logic Summary: Executes a DELETE FROM query across the entire INCIDENT_HISTORY table.
    """
    reconstructor.history_db.clear_history()
    return {"status": "success", "message": "History cleared successfully"}

@app.get("/api/export/history")
def export_history_csv(limit: int = 5000, offset: int = 0, node_id: str = None, anomaly_type: str = None, severity: str = None, date_filter: str = None, time_chunk: str = None):
    from fastapi.responses import FileResponse
    import time as _time, tempfile
    rows = reconstructor.history_db.query_history(limit=limit, offset=offset, node_id=node_id, anomaly_type=anomaly_type, severity=severity, date_filter=date_filter, time_chunk=time_chunk)
    headers = ['Timestamp','Node ID','Attack Vector','Severity','Trust Before','Trust After','Trust Delta','HTTP Status','JSON Status','Schema','Latency (ms)','Identity']
    lines = [','.join(headers)]
    for r in rows:
        vals = [r.get('timestamp',''), str(r.get('node_id','')), r.get('anomaly_type',''), r.get('severity',''),
                str(round(r.get('trust_before',0))), str(round(r.get('trust_after',0))), str(round(r.get('trust_delta',0))),
                str(r.get('http_status','')), r.get('json_status',''), r.get('schema_version',''),
                str(round(r['latency_ms'])) if r.get('latency_ms') is not None else '', r.get('decoded_identity','')]
        lines.append(','.join(['"' + v.replace('"', '""') + '"' for v in vals]))
    fname = f"aegis_history_{int(_time.time())}.csv"
    filepath = os.path.join(tempfile.gettempdir(), fname)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('\n'.join(lines))
    return FileResponse(path=filepath, filename=fname, media_type="text/csv")

# Temporary CSV store for two-step stream export
_csv_store = {}

@app.post("/api/export/prepare")
async def prepare_csv(content: str = Form(...), filename: str = Form("export.csv")):
    import uuid, tempfile
    file_id = uuid.uuid4().hex[:8]
    filepath = os.path.join(tempfile.gettempdir(), filename)
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(content)
    _csv_store[file_id] = {"path": filepath, "filename": filename}
    return {"url": f"/api/export/file/{file_id}/{filename}"}

@app.get("/api/export/file/{file_id}/{filename}")
def serve_csv_file(file_id: str, filename: str):
    from fastapi.responses import FileResponse
    data = _csv_store.pop(file_id, None)
    if not data or not os.path.exists(data["path"]):
        return Response(content="File expired", status_code=404)
    return FileResponse(path=data["path"], filename=data["filename"], media_type="text/csv")

@app.get("/api/detect")
def get_attribution():
    """
    Purpose: Returns the current convicted Shadow Controllers based on Mathematical Engine.
    """
    try:
        active_nids = list(reconstructor.nodes.keys())
        results = reconstructor.attribution_engine.execute_attribution(active_nids, reconstructor.tick_counter)
        sorted_suspects = sorted(results.values(), key=lambda x: x["final_score"], reverse=True)
        return {"status": "success", "data": sorted_suspects[:10]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/metrics")
def get_metrics():
    """
    Purpose: Returns engine tracking metrics.
    """
    try:
        edges = len(reconstructor.attribution_engine.graph_engine.edges)
    except Exception:
        edges = len(reconstructor.propagation_graph)
        
    return {
        "status": "success", 
        "data": {
            "tick": getattr(reconstructor, 'tick_counter', 0),
            "tracked_nodes": len(reconstructor.nodes),
            "propagation_edges": edges
        }
    }


@app.post("/api/simulate/remove_node/{node_id}")
async def remove_node_simulation(node_id: str):
    """
    Purpose: Drops the target node from graph engine to visually simulate a Kill-Switch operation.
    """
    try:
        reconstructor.attribution_engine.graph_engine.kill_node(node_id)
        # We can also track it in reconstructor if needed:
        if not hasattr(reconstructor, 'killed_nodes'):
            reconstructor.killed_nodes = set()
        reconstructor.killed_nodes.add(int(node_id))
        
        # Optionally force a tick broadcast or wait for loop
        return {"status": "success", "message": f"Killed node {node_id} network edges"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def simulation_loop():
    """
    Purpose: Asynchronous daemon dictating engine progression.
    Inputs: Implicit ingestion from batch generator.
    Outputs: Mutated reconstructed State.
    Logic Summary: Evaluates pause state, extracts batched datasets, pushes to reconstructor pipeline, formats dictionary, and broadcasts iteratively to listening WebSocket client pool.
    """
    loop_status["running"] = True
    print("[AEGIS] Simulation loop STARTED")
    while True:
        try:
            if not is_paused:
                batch = streamer.get_batch()
                if batch:
                    state = reconstructor.process_batch(batch)
                    state["total_registry_nodes"] = len(streamer.registry)
                    state["stream_mode"] = streamer.stream_mode
                    state["total_events"] = streamer.get_total_events()

                    loop_status["ticks"] += 1
                    loop_status["last_tick_time"] = str(asyncio.get_event_loop().time())
                    loop_status["clients_count"] = len(clients)

                    if clients:
                        dead_clients = []
                        for c in clients:
                            try:
                                await c.send_json(state)
                            except Exception:
                                dead_clients.append(c)
                        for c in dead_clients:
                            clients.remove(c)
                else:
                    print("[AEGIS] WARNING: get_batch() returned empty")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            print(f"[AEGIS] SIMULATION LOOP ERROR: {error_msg}")
            loop_status["last_error"] = error_msg

        await asyncio.sleep(1.5)  # Multi-node batch every 1.5 seconds

@app.on_event("startup")
async def startup_event():
    """
    Purpose: Triggers event loops on system initialization.
    Inputs: API boot sequence.
    Outputs: Execution daemon.
    Logic Summary: Deploys asyncio simulation task decoupled from blocking synchronous network handlers.
    """
    print("[AEGIS] Starting simulation loop task...")
    asyncio.create_task(simulation_loop())

@app.get("/api/debug")
def debug_status():
    """Debug endpoint to check simulation loop health remotely."""
    return {
        "loop_status": loop_status,
        "streamer_position": streamer.get_current_position(),
        "streamer_total": streamer.get_total_events(),
        "streamer_logs_loaded": len(streamer.logs),
        "streamer_registry_loaded": len(streamer.registry),
        "connected_clients": len(clients),
        "is_paused": is_paused,
        "reconstructor_tick": reconstructor.tick_counter,
        "reconstructor_nodes": len(reconstructor.nodes)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Purpose: Real-time telemetry pipe channel.
    Inputs: Upgrading HTTP HTTP1.1 client request.
    Outputs: Active WS socket.
    Logic Summary: Manages connection registry array `clients` mapping, automatically invoking system reset logic per connection for seamless presentations, preventing ghost loops on client disconnection.
    """
    await websocket.accept()
    clients.append(websocket)
    print("Dashboard connected. Resetting engine and dataset to 0 for a fresh start...")
    global is_paused
    is_paused = False
    streamer.seek(0)
    reconstructor.reset()
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)
    except Exception:
        if websocket in clients:
            clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
