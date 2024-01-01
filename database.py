import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# load env variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
USER = os.getenv("MONGO_USER")
PASSWORD = os.getenv("MONGO_PASSWORD")
HOST = os.getenv("MONGO_HOST")
DATABASE = os.getenv("DATABASE")
uri = f"mongodb+srv://{USER}:{PASSWORD}@{HOST}/{DATABASE}?retryWrites=true&w=majority"

# Create a new client and connect to the server
mongoClient = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    mongoClient.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# access collection user
db = mongoClient[DATABASE]
userCollection = db["users"]
wordCollection = db["words"]

# Check if the token was loaded successfully
if not TOKEN:
    print("Error: Discord token not found in .env file")
else:
    print("Discord token loaded successfully")
