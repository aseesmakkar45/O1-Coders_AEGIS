import csv, base64
from collections import defaultdict

counts = defaultdict(list)
with open('../Aegis/node_registry.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        node_id = int(row['node_uuid'])
        ua = row['user_agent']
        b64 = ua.split(' ')[-1] if ' ' in ua else ua
        try:
            dec = base64.b64decode(b64).decode()
        except:
            dec = b64
        counts[dec].append((node_id, row['is_infected'] == 'True'))

with open('dup_analysis.txt', 'w') as f:
    for k, v in counts.items():
        if len(v) > 1:
            f.write(f"Identity {k}: {v}\n")
