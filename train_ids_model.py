import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# LOAD
df = pd.read_csv("ids_data.csv")

X = df[[
    "request_count",
    "endpoint_hits",
    "global_traffic",
    "hour"
]]

y = df["label"]

# SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# SCALE
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# MODEL (Multi-class)
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    random_state=42
)

model.fit(X_train, y_train)

# EVALUATE
y_pred = model.predict(X_test)

print("\n🎯 Accuracy:", accuracy_score(y_test, y_pred))
print("\n📊 Report:\n", classification_report(y_test, y_pred))

# SAVE
joblib.dump(model, "ddos_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("✅ Multi-class model saved!")