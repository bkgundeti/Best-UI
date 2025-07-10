import os
import pymongo
from dotenv import load_dotenv
from agents.logger import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger("recommender_agent", "logs/recommender_agent.log")

class RecommenderAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("RECOMMENDER_DB_NAME")
        self.collection_name = os.getenv("RECOMMENDER_COLLECTION_NAME")

        if not all([self.mongo_uri, self.db_name, self.collection_name]):
            raise ValueError("❌ MongoDB environment variables not set correctly in .env file.")

    def _fetch_model_dataset(self):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            data = list(collection.find({}, {"_id": 0}))  # Exclude _id field
            logger.info(f"✅ Fetched {len(data)} models from MongoDB collection `{self.collection_name}`.")
            return data
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            print(f"❌ MongoDB connection failed: {e}")
            return []

    def recommend_models(self, analyzed_user_input: str):
        dataset = self._fetch_model_dataset()
        if not dataset:
            logger.warning("⚠️ No dataset available for recommendation.")
            return []

        prompt = f"""
You are an AI expert. From the following dataset, pick the top 4–5 models suitable for the user's requirement.
If the requirement is for multiple tasks, select models with both capabilities.

User needs:
{analyzed_user_input}

AI Model List:
{dataset}

Reply with a bullet list of model names and 1-line reason each.
"""

        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant for AI model recommendation."},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            result = response.choices[0].message.content
            logger.info("✅ Recommended models:\n" + result)
            return result
        except Exception as e:
            logger.error(f"❌ GPT recommendation error: {e}")
            print(f"❌ GPT recommendation error: {e}")
            return "Model recommendation failed."
