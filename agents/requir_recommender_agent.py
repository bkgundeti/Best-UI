import sys
import os
import json
import pymongo
from dotenv import load_dotenv
from agents.logger import get_logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
            data = list(collection.find({}, {"_id": 0}))
            logger.info(f"✅ Fetched {len(data)} models from MongoDB.")
            return data
        except Exception as e:
            logger.error(f"❌ MongoDB fetch error: {e}")
            return []

    def recommend_models(self, analyzed_input: str, alternative_mode=False, exclude_model_name=None):
        dataset = self._fetch_model_dataset()
        if not dataset:
            logger.warning("⚠️ Empty dataset. Cannot proceed.")
            return []

        # Optional filtering for alternatives
        if alternative_mode and exclude_model_name:
            dataset = [model for model in dataset if model.get("Model_Name") != exclude_model_name]
            logger.info(f"⚙️ Filtered dataset to exclude previously suggested model: {exclude_model_name}")

        system_prompt = (
            "You are an expert AI assistant trained to recommend the best AI models based on user needs.\n"
            "- You will receive a list of models (JSON) and a user requirement.\n"
            "- Recommend ONLY 3 to 5 models.\n"
            "- Avoid repeating the same model in multiple runs.\n"
            "- Output should be valid JSON array: each item must contain `Model Name` and `Reason`.\n"
            "- Avoid suggesting image models if user only asked for text tasks.\n"
            "- Focus on text generation/summarization models if required.\n\n"
        )

        user_prompt = f"""
User Requirement:
\"\"\"{analyzed_input}\"\"\"

Model Dataset (JSON):
{json.dumps(dataset)}

Instructions:
- Match model capabilities with the user's task.
- Prioritize accuracy, budget, speed, and purpose.
- Avoid models irrelevant to the use-case.
- Output Format (must be JSON list):
[
  {{
    "Model Name": "<name>",
    "Reason": "<1-line reason>"
  }},
  ...
]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            result = response.choices[0].message.content.strip()
            logger.info("✅ Raw GPT Recommendation:\n" + result)

            # Try to parse as JSON list
            try:
                recommendations = json.loads(result)
                if isinstance(recommendations, list):
                    return recommendations
                else:
                    raise ValueError("GPT response is not a list")
            except json.JSONDecodeError as decode_err:
                logger.warning(f"⚠️ Failed to parse GPT response as JSON: {decode_err}")
                return [{"message": "Failed to parse model recommendations."}]

        except Exception as e:
            logger.error(f"❌ GPT model recommendation error: {e}")
            return [{"message": "GPT model recommendation failed."}]
