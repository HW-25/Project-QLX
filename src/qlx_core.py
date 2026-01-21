from flask import Flask, request, jsonify, render_template_string
import sqlite3
import time

app = Flask(__name__)
DB_FILE = "qlx_network.db"

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS nodes 
                 (uuid TEXT PRIMARY KEY, pwr REAL, valor REAL, last_seen REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- THE "NETWORK" DASHBOARD (C-BRUTALIST V2) ---
DASHBOARD_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>QLX-CORE | GLOBAL NETWORK</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { background-color: #000; color: #00FF00; font-family: 'Courier New', monospace; padding: 30px; }
        h1 { font-size: 20px; border-bottom: 2px solid #00FF00; display: inline-block; padding-bottom: 5px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px; }
        .node-card { border: 1px solid #004400; padding: 15px; background: #050505; }
        .node-card.active { border-color: #00FF00; box-shadow: 0 0 10px #004400; }
        .uuid { font-size: 10px; color: #888; margin-bottom: 10px; }
        .metric { font-size: 18px; color: #FFF; }
        .label { font-size: 9px; color: #00FF00; text-transform: uppercase; }
        .footer { margin-top: 40px; font-size: 10px; color: #444; }
    </style>
</head>
<body>
    <h1>QLX-CORE :: ACTIVE_NETWORK_FLEET</h1>
    <div class="grid">
        {% for node in nodes %}
        <div class="node-card {% if now - node[3] < 30 %}active{% endif %}">
            <div class="uuid">NODE_ID: {{ node[0] }}</div>
            <div>
                <span class="label">Power:</span> <span class="metric">{{ node[1] }} mW</span>
            </div>
            <div>
                <span class="label">Accumulated:</span> <span class="metric" style="color:#FFAA00;">{{ "%.6f"|format(node[2]) }} QLX</span>
            </div>
            <div style="font-size:9px; margin-top:10px;">
                STATUS: {% if now - node[3] < 30 %}ONLINE{% else %}TIMED_OUT{% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    <div class="footer">> DATABASE: SQLITE3 | NODES_TOTAL: {{ nodes|length }} | SYSTEM_CLOCK: {{ now }}</div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM nodes ORDER BY last_seen DESC")
    nodes = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_UI, nodes=nodes, now=time.time())

@app.route('/api/uplink', methods=['POST'])
def uplink():
    data = request.json
    uid = data['auth']['uuid']
    pwr = data['telemetry']['avg_mw']
    val = data['telemetry']['total_valor']
    ts = data['timestamp']

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # UPSERT Logic (Update if exists, Insert if new)
    c.execute("INSERT OR REPLACE INTO nodes (uuid, pwr, valor, last_seen) VALUES (?, ?, ?, ?)", 
              (uid, pwr, val, ts))
    conn.commit()
    conn.close()
    return jsonify({"status": "verified"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)