from pymongo import MongoClient

uri = "mongodb+srv://admin:cloud123@cloud-ids.cbiyo7s.mongodb.net/cloud_ids?retryWrites=true&w=majority"
client = MongoClient(uri)

try:
    db = client.cloud_ids
    print("Databases:", client.list_database_names())
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)