import pandas as pd
from sklearn.ensemble import IsolationForest
from pymongo import MongoClient
import joblib

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://admin:cloud123@cloud-ids.cbiyo7s.mongodb.net/")
db = client["cloud_ids"]

# Load traffic logs
data = list(db.traffic_logs.find())

df = pd.DataFrame(data)

if df.empty:
    print("No data available to train model.")
    exit()

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Feature engineering
df["hour"] = df["timestamp"].dt.hour

features = df[["request_count", "hour"]]

# Train anomaly detection model
model = IsolationForest(contamination=0.02)

model.fit(features)

# Save model
joblib.dump(model, "ddos_model.pkl")

print("✅ ML Model Trained Successfully")