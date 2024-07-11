from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import DB_URL

client = MongoClient(DB_URL)

def check_server_status():
    print("Scanning database'server health.")
    try:
        info = client.server_info() # Forces a call.
        print("Server still working.")
    except ConnectionFailure:
        print("Server is down.")