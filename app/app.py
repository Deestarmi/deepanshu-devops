"""
DevOps 101 — Simple Flask App
Purpose: learn Docker → K8s → Helm → GitOps one step at a time
"""
import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

ENV     = os.getenv("APP_ENV",     "local")
VERSION = os.getenv("APP_VERSION", "v1")
COLOR   = os.getenv("APP_COLOR",   "#0078d4")   # change per environment!

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>DevOps 101</title>
  <style>
    body { font-family: sans-serif; display:flex; align-items:center;
           justify-content:center; height:100vh; margin:0;
           background: {{ color }}11; }
    .box { background: white; border: 3px solid {{ color }};
           border-radius: 16px; padding: 40px 60px; text-align: center;
           box-shadow: 0 4px 20px {{ color }}33; }
    h1   { color: {{ color }}; margin: 0 0 8px; font-size: 2.5rem; }
    .env { background: {{ color }}; color: white; border-radius: 20px;
           padding: 4px 16px; font-size: 1rem; display: inline-block; margin: 8px 0; }
    p    { color: #555; margin: 4px 0; }
  </style>
</head>
<body>
  <div class="box">
    <h1>🚀 DevOps 101</h1>
    <div class="env">{{ env }}</div>
    <p>Version: <strong>{{ version }}</strong></p>
    <p>Hostname: <strong>{{ hostname }}</strong></p>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML,
        env=ENV, version=VERSION, color=COLOR,
        hostname=os.uname().nodename)

@app.route("/health")
def health():
    return jsonify(status="ok", env=ENV, version=VERSION)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=(ENV == "local"))
