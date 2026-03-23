from flask import Flask, jsonify, request, render_template, session, redirect
from flask_pymongo import PyMongo
from collections import defaultdict, deque, Counter
from datetime import datetime
import joblib
import pandas as pd
import requests
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ==============================
# MongoDB Atlas
# ==============================
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# ==============================
# Global Structures
# ==============================
traffic_window = defaultdict(deque)
endpoint_window = defaultdict(lambda: defaultdict(deque))
blacklist = set()
global_traffic = deque()

DDOS_THRESHOLD = 10
LOGIN_THRESHOLD = 10
ENDPOINT_THRESHOLD = 10
GLOBAL_DDOS_THRESHOLD = 30

# ==============================
# LOAD MODEL + SCALER
# ==============================
try:
    model = joblib.load("ddos_model.pkl")
    scaler = joblib.load("scaler.pkl")
    print("✅ ML Model + Scaler Loaded")
except:
    model = None
    scaler = None
    print("⚠ ML Model not found")

# ==============================
# ATTACK TYPE MAPPING
# ==============================
ATTACK_TYPES = {
    0: "Normal",
    1: "DDoS Attack",
    2: "Brute Force",
    3: "Endpoint Flood"
}

# ==============================
# ML Detection
# ==============================
def detect_ml_attack(ip, request_count):

    if not model or not scaler:
        return None, 0

    features = [[
        request_count,
        len(endpoint_window[ip]),
        len(global_traffic),
        datetime.utcnow().hour
    ]]

    features = scaler.transform(features)

    prediction = model.predict(features)[0]

    confidence = 0
    if hasattr(model, "predict_proba"):
        confidence = max(model.predict_proba(features)[0])

    return prediction, float(confidence)

# ==============================
# Block IP + GEO
# ==============================
def block_ip(ip, reason, ml_score=0):

    print(f"[ALERT] Blocking IP: {ip} | Reason: {reason}")
    blacklist.add(ip)

    # System level block
    try:
        os.system(f"sudo iptables -A INPUT -s {ip} -j DROP")
    except:
        pass

    # Severity
    severity = "Low"
    if "DDoS" in reason:
        severity = "High"
    elif "Brute" in reason or "Endpoint" in reason:
        severity = "Medium"
    elif "ML" in reason:
        severity = "Medium"

    country = city = lat = lon = None

    try:
        geo = requests.get(f"https://ipinfo.io/{ip}/json", timeout=2).json()
        country = geo.get("country")
        city = geo.get("city")

        if "loc" in geo:
            loc = geo["loc"].split(",")
            lat = float(loc[0])
            lon = float(loc[1])
    except:
        pass

    try:
        mongo.db.alerts.insert_one({
            "type": reason,
            "severity": severity,
            "ip": ip,
            "country": country,
            "city": city,
            "lat": lat,
            "lon": lon,
            "endpoint": request.path,
            "ml_score": ml_score,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print("MongoDB error:", e)

# ==============================
# Traffic Logging
# ==============================
def log_traffic(ip, endpoint, count):
    try:
        mongo.db.traffic_logs.insert_one({
            "ip": ip,
            "endpoint": endpoint,
            "request_count": count,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print("Traffic log error:", e)

# ==============================
# Protect Admin
# ==============================
@app.before_request
def protect_admin():
    if request.path.startswith("/admin"):
        if request.path == "/admin/login":
            return
        if not session.get("admin_logged_in"):
            return redirect("/admin/login")

# ==============================
# MAIN IDS LOGIC
# ==============================
@app.before_request
def monitor():

    ip = request.remote_addr
    endpoint = request.path
    now = datetime.utcnow()

    if endpoint.startswith("/admin"):
        return

    if ip in blacklist:
        return jsonify({"status": "blocked"}), 403

    traffic_window[ip].append(now)
    endpoint_window[ip][endpoint].append(now)

    request_count = len(traffic_window[ip])
    log_traffic(ip, endpoint, request_count)

    # ================= ML Detection =================
    prediction, confidence = detect_ml_attack(ip, request_count)

    if prediction is not None and prediction != 0:
        attack_type = ATTACK_TYPES.get(prediction, "Unknown Attack")

        block_ip(ip, f"ML {attack_type}", confidence)

        return jsonify({
            "alert": attack_type,
            "confidence": confidence
        }), 403

    # ================= Global DDoS =================
    global_traffic.append(now)

    while global_traffic and (now - global_traffic[0]).seconds > 10:
        global_traffic.popleft()

    if len(global_traffic) > GLOBAL_DDOS_THRESHOLD:
        block_ip(ip, "Distributed DDoS")
        return jsonify({"alert": "Distributed DDoS"}), 403

    # ================= Cleanup =================
    while traffic_window[ip] and (now - traffic_window[ip][0]).seconds > 10:
        traffic_window[ip].popleft()

    while endpoint_window[ip][endpoint] and (now - endpoint_window[ip][endpoint][0]).seconds > 10:
        endpoint_window[ip][endpoint].popleft()

    # ================= Rule-Based =================
    if len(traffic_window[ip]) > DDOS_THRESHOLD:
        block_ip(ip, "DDoS Attack")
        return jsonify({"alert": "ddos"}), 403

    if endpoint == "/login" and len(endpoint_window[ip][endpoint]) > LOGIN_THRESHOLD:
        block_ip(ip, "Login Brute Force")
        return jsonify({"alert": "bruteforce"}), 403

    if len(endpoint_window[ip][endpoint]) > ENDPOINT_THRESHOLD:
        block_ip(ip, f"Endpoint Flood {endpoint}")
        return jsonify({"alert": "endpoint flood"}), 403
    print(f"IP: {ip}, Requests: {len(traffic_window[ip])}")
    print(f"IP: {ip}")
    print(f"Count: {len(traffic_window[ip])}")
# ==============================
# ROUTES
# ==============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/products")
def products():
    return jsonify({"message": "products page"})

@app.route("/cart")
def cart():
    return jsonify({"message": "cart page"})

@app.route("/checkout")
def checkout():
    return jsonify({"message": "checkout page"})

# ==============================
# USER LOGIN
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "user" and request.form.get("password") == "user123":
            return redirect("/")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# ==============================
# ADMIN
# ==============================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")

@app.route("/admin/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ==============================
# APIs
# ==============================
@app.route("/admin/live-data")
def live_data():

    alerts = list(mongo.db.alerts.find())

    total = len(alerts)
    ddos = brute = ml = 0
    rule_based = 0
    ml_based = 0

    ip_counter = Counter()
    endpoint_counter = Counter()
    timeline = {}

    for a in alerts:

        t = a.get("type", "")

        # ✅ ML vs Rule separation
        if "ML" in t:
            ml += 1
            ml_based += 1
        else:
            rule_based += 1

        # ✅ Attack types
        if "DDoS" in t:
            ddos += 1

        if "Brute" in t:
            brute += 1

        ip_counter[a.get("ip", "unknown")] += 1
        endpoint_counter[a.get("endpoint", "/")] += 1

        ts = a.get("timestamp")
        if ts:
            key = str(ts)[:19]
            timeline[key] = timeline.get(key, 0) + 1

    return jsonify({
        "total_alerts": total,
        "ddos_attacks": ddos,
        "brute_force_attacks": brute,
        "ml_attacks": ml,
        "rule_attacks": rule_based,
        "blocked_ips": list(blacklist),
        "top_ips": ip_counter.most_common(5),
        "top_endpoints": endpoint_counter.most_common(5),
        "timeline": timeline,
        "ml_enabled": True
    })
    
@app.route("/admin/attack-map")
def attack_map():

    alerts = list(mongo.db.alerts.find())
    locations = []

    for a in alerts:
        if a.get("lat") and a.get("lon"):
            locations.append({
                "lat": a["lat"],
                "lon": a["lon"],
                "ip": a["ip"],
                "type": a["type"],
                "severity": a.get("severity", "Low")
            })

    return jsonify(locations)

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run()