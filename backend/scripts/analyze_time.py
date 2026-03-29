import csv

logs = []
with open('../Aegis/system_logs.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        logs.append(row)

target_nodes = ['416', '345', '57', '339', '75', '228', '97', '248', '130', '209', '207', '354', '317', '382']

for log in logs:
    if log['node_id'] in target_nodes and (log['http_response_code'] != '200' or float(log['response_time_ms']) > 180):
        print(f"Log {log['log_id']} | Node {log['node_id']} | HTTP {log['http_response_code']} | Latency {log['response_time_ms']}")
