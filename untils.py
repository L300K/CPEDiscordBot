import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import DB_URL

client = MongoClient(DB_URL)

def check_server_status():
    logging.debug("Scanning DB server health")
    try:
        info = client.server_info() # Forces a call.
        logging.debug(info)
    except ConnectionFailure:
        logging.error("server is down.")
    logging.debug("Finish Scanning")