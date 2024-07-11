from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View
import logging
from config import DB_URL, TOKEN, CHANNEL
from untils import check_server_status

logging.basicConfig(level=logging.DEBUG)
check_server_status()