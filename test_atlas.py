from pymongo import MongoClient

uri = "mongodb+srv://admin:cloud123@cloud-ids.cbiyo7s.mongodb.net/cloud_ids?retryWrites=true&w=majority"

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    print("Databases:", client.list_database_names())
    print("✅ Connection Successful")
except Exception as e:
    print("❌ Connection Failed:", e)