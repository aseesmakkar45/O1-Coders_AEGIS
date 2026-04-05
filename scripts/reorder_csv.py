"""
Analyze data.csv to find attack-triggering events, then reorder to front-load them.
"""
import csv, os, base64, shutil
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "Aegis")
SESSION = 30

# --- Load registry ---
registry = {}
decoded_to_nodes = defaultdict(list)
with open(os.path.join(DATA_DIR, "node_registry.csv"), "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        nid = int(row["node_uuid"])
        ua = row["user_agent"]
        b64 = ua.split(" ")[-1] if " " in ua else ua
        try: decoded = base64.b64decode(b64).decode("utf-8")
        except: decoded = "INVALID"
        registry[nid] = {"decoded_id": decoded, "is_infected": row["is_infected"].strip() == "True"}
        if decoded not in ("UNKNOWN", "INVALID"):
            decoded_to_nodes[decoded].append(nid)

# --- Load schema config ---
schema_config = []
with open(os.path.join(DATA_DIR, "schema_config.csv"), "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        schema_config.append({"version": int(row["version"]), "time_start": int(row["time_start"]), "active_column": row["active_column"]})

# --- Load events ---
raw_rows = []
events = []
with open(os.path.join(DATA_DIR, "data.csv"), "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        log_id = int(row["log_id"])
        node_id = int(row["node_id"])
        schema_ver, active_col = 1, "load_val"
        for sc in schema_config:
            if log_id >= sc["time_start"]:
                schema_ver, active_col = sc["version"], sc["active_column"]
        raw_load = row.get(active_col, "")
        load_value = float(raw_load) if raw_load else 0.0
        reg = registry.get(node_id, {})
        events.append({
            "log_id": log_id, "node_id": node_id,
            "lat": int(row["response_time_ms"]), "load": load_value,
            "http": int(row["http_response_code"]),
            "schema": f"v{schema_ver}",
            "decoded_id": reg.get("decoded_id", "UNKNOWN"),
        })
        raw_rows.append(row)

print(f"Loaded {len(events)} events, {len(set(e['node_id'] for e in events))} unique nodes")

# --- Group events by node ---
node_evts = defaultdict(list)
for i, e in enumerate(events):
    node_evts[e["node_id"]].append(i)

# --- Find candidates ---
ddos_nodes = defaultdict(list)  # lat>210, load>0.85
spike_nodes = defaultdict(list)  # lat>210, load<=0.85
for i, e in enumerate(events):
    if e["lat"] > 210 and e["load"] > 0.85: ddos_nodes[e["node_id"]].append(i)
    elif e["lat"] > 210 and e["load"] <= 0.85: spike_nodes[e["node_id"]].append(i)

# Schema rotation: same node with v1 AND v2
node_schemas = defaultdict(lambda: defaultdict(list))
for i, e in enumerate(events):
    node_schemas[e["node_id"]][e["schema"]].append(i)
schema_rot = {n: s for n, s in node_schemas.items() if len(s) > 1}

# Identity theft: different nodes sharing decoded_id
theft = {d: ns for d, ns in decoded_to_nodes.items() if len(ns) > 1}

print(f"\nDDOS candidates: {len(ddos_nodes)} nodes")
print(f"LATENCY_SPIKE candidates: {len(spike_nodes)} nodes")
print(f"SCHEMA_ROTATION candidates: {len(schema_rot)} nodes")
print(f"IDENTITY_THEFT pairs: {len(theft)}")
if theft:
    for d, ns in list(theft.items())[:3]:
        print(f"  {d} -> nodes {ns}")

# --- Select sessions ---
used = set()
sessions = []

# DDOS
if ddos_nodes:
    nid = max(ddos_nodes, key=lambda n: len(ddos_nodes[n]))
    evts = node_evts[nid]
    first_ddos = ddos_nodes[nid][0]
    pos = evts.index(first_ddos) if first_ddos in evts else 0
    start = max(0, pos - 5)
    sessions.append((nid, evts[start:start+SESSION], "DDOS"))
    used.add(nid)
    print(f"\nDDOS node: {nid} ({len(evts[start:start+SESSION])} events)")

# LATENCY_SPIKE
avail = {n: e for n, e in spike_nodes.items() if n not in used}
if avail:
    nid = max(avail, key=lambda n: len(avail[n]))
    evts = node_evts[nid]
    first = avail[nid][0]
    pos = evts.index(first) if first in evts else 0
    start = max(0, pos - 5)
    sessions.append((nid, evts[start:start+SESSION], "SPIKE"))
    used.add(nid)
    print(f"SPIKE node: {nid} ({len(evts[start:start+SESSION])} events)")

# SCHEMA_ROTATION
avail_sr = {n: s for n, s in schema_rot.items() if n not in used}
if avail_sr:
    nid = max(avail_sr, key=lambda n: min(len(v) for v in avail_sr[n].values()))
    v1 = node_schemas[nid].get("v1", [])
    v2 = node_schemas[nid].get("v2", [])
    session = v1[:SESSION//2] + v2[:SESSION//2]
    sessions.append((nid, session, "SCHEMA"))
    used.add(nid)
    print(f"SCHEMA node: {nid} (v1={len(v1[:SESSION//2])}, v2={len(v2[:SESSION//2])})")

# IDENTITY_THEFT
if theft:
    for did, nodes in theft.items():
        avail_n = [n for n in nodes if n not in used]
        if len(avail_n) >= 2:
            a, b = avail_n[0], avail_n[1]
            sessions.append((a, node_evts[a][:SESSION], "ID_OWNER"))
            sessions.append((b, node_evts[b][:SESSION], "ID_THIEF"))
            used.update([a, b])
            print(f"IDENTITY pair: {a} -> {b} (decoded_id={did})")
            break

# NORMAL baseline nodes
normal = [n for n in node_evts if n not in used and n not in ddos_nodes and n not in spike_nodes and len(node_evts[n]) >= SESSION]
for nid in normal[:2]:
    sessions.append((nid, node_evts[nid][:SESSION], "NORMAL"))
    used.add(nid)
    print(f"NORMAL node: {nid}")

# --- Interleave ---
front = set()
iters = [iter(s[1]) for s in sessions]
interleaved = []
active = list(range(len(iters)))
while active:
    nxt = []
    for i in active:
        try:
            idx = next(iters[i])
            interleaved.append(idx)
            front.add(idx)
            nxt.append(i)
        except StopIteration: pass
    active = nxt

remaining = [i for i in range(len(events)) if i not in front]
final = interleaved + remaining
print(f"\nFront: {len(interleaved)} events, Remaining: {len(remaining)}, Total: {len(final)}")

# --- Backup & Write ---
backup = os.path.join(DATA_DIR, "data_original_backup.csv")
if not os.path.exists(backup):
    shutil.copy2(os.path.join(DATA_DIR, "data.csv"), backup)
    print(f"Backup saved: {backup}")

with open(os.path.join(DATA_DIR, "data.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for idx in final:
        w.writerow(raw_rows[idx])
print("Wrote reordered data.csv")

# --- Preview ---
print(f"\n=== FIRST 40 EVENTS ===")
for i in range(min(40, len(final))):
    e = events[final[i]]
    tag = ""
    if e["lat"] > 210 and e["load"] > 0.85: tag = "DDOS"
    elif e["lat"] > 210 and e["load"] <= 0.85: tag = "SPIKE"
    print(f"  [{i:3d}] N-{e['node_id']:4d} lat={e['lat']:4d} load={e['load']:.2f} http={e['http']} {e['schema']} {tag}")
