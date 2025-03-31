import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster0.4e885.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)


db = client['IS3107-GROUP11']

hawker_centre_db = db['hawker_centre']
cleaning_schedule_db = db['cleaning_schedule']
hawker_stall_db = db['hawker_stall']
opening_hours_db = db['opening_hours']
reviews_db = db['reviews']
user_history_db = db['user_history']