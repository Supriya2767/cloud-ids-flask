import pandas as pd
import random

data = []

# ======================
# NORMAL TRAFFIC (0)
# ======================
for _ in range(5000):
    data.append([
        random.randint(1, 20),     # request_count
        random.randint(1, 5),      # endpoint_hits
        random.randint(20, 100),   # global_traffic
        random.randint(0, 23),     # hour
        0
    ])

# ======================
# DDoS (1)
# ======================
for _ in range(3000):
    data.append([
        random.randint(80, 200),
        random.randint(5, 15),
        random.randint(200, 500),
        random.randint(0, 23),
        1
    ])

# ======================
# BRUTE FORCE (2)
# ======================
for _ in range(2000):
    data.append([
        random.randint(20, 60),
        1,   # same endpoint
        random.randint(50, 150),
        random.randint(0, 23),
        2
    ])

# ======================
# ENDPOINT FLOOD (3)
# ======================
for _ in range(2000):
    data.append([
        random.randint(40, 100),
        random.randint(15, 50),
        random.randint(100, 300),
        random.randint(0, 23),
        3
    ])

df = pd.DataFrame(data, columns=[
    "request_count",
    "endpoint_hits",
    "global_traffic",
    "hour",
    "label"
])

df.to_csv("ids_data.csv", index=False)

print("✅ Multi-class dataset generated!")