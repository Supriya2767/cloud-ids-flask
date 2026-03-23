from pymongo import MongoClient

uri = "mongodb+srv://admin:cloud123@cloud-ids.cbiyo7s.mongodb.net/cloud_ids?retryWrites=true&w=majority&authSource=admin"

try:
    client = MongoClient(uri)
    client.admin.command("ping")
    print("✅ Connected successfully!")
except Exception as e:
    print("❌ Connection failed:", e)