import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymongo
from dotenv import load_dotenv
from agents.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("recommender_agent", "logs/recommender_agent.log")

class RecommenderAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("RECOMMENDER_DB_NAME")
        self.collection_name = os.getenv("RECOMMENDER_COLLECTION_NAME")

        if not all([self.mongo_uri, self.db_name, self.collection_name]):
            raise ValueError("MongoDB environment variables not set correctly in .env file.")

    def _fetch_model_dataset(self):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            data = list(collection.find({}, {"_id": 0}))  # Exclude _id
            logger.info(f"Fetched {len(data)} models from `{self.collection_name}`.")
            return data
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return []

    def recommend_models(self, analyzed_user_input: str):
        dataset = self._fetch_model_dataset()
        if not dataset:
            logger.warning("No dataset available for recommendation.")
            return []

        prompt = f"""
You are an AI model selection expert. Based on the user's analyzed input, recommend 4–5 suitable models from the dataset.

User Requirement:
\"\"\"{analyzed_user_input}\"\"\"

Model Dataset (each model is a dictionary object):
{dataset}

Instructions:
- Consider cost, speed, accuracy, and capability (e.g. image, text, multimodal).
- Match model strength with user need. Do not recommend the same model always.
- Explain each model's suitability in 1 line.

Output Format:
- Model Name: <model>
  Reason: <short reason>
"""

        try:
            messages = [
                {"role": "system", "content": "You are an AI assistant for selecting suitable models."},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            result = response.choices[0].message.content
            logger.info("Recommended models:\n" + result)
            return result
        except Exception as e:
            logger.error(f"GPT model recommendation error: {e}")
            return "Model recommendation failed."
