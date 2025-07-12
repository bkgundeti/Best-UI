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

    def _is_model_request(self, analyzed_input: str) -> bool:
        """Check if input is relevant for model recommendation."""
        keywords = [
            "generate", "summarize", "translate", "image", "audio",
            "speech", "text", "content", "model", "ai", "voice", "task", "recommend"
        ]
        return any(k in analyzed_input.lower() for k in keywords)

    def recommend_models(self, analyzed_input: str, alternative_mode=False, exclude_model_name=None):
        # 🧠 Step 1: Input Check
        if not self._is_model_request(analyzed_input):
            logger.info("🛑 Input does not request model recommendation. Skipping suggestion.")
            return [{"message": "No model recommendation needed based on your input."}]

        # 🧠 Step 2: Fetch Dataset
        dataset = self._fetch_model_dataset()
        if not dataset:
            logger.warning("⚠️ Empty dataset. Cannot proceed.")
            return [{"message": "Model database is empty. Please try again later."}]

        # 🧠 Step 3: Optional Alternative Filtering
        if alternative_mode and exclude_model_name:
            dataset = [model for model in dataset if model.get("Model_Name") != exclude_model_name]
            logger.info(f"⚙️ Filtered out model: {exclude_model_name}")

        # 🧠 Step 4: Prompt Construction
        system_prompt = (
            "You are an expert AI assistant trained to recommend the best AI models based on user needs.\n"
            "- You will receive a JSON list of models and a user requirement.\n"
            "- Recommend ONLY 3 to 5 relevant models based on the task.\n"
            "- Output only a valid JSON list: each item must have 'Model Name' and 'Reason'.\n"
            "- Do not include irrelevant models.\n"
            "- Avoid recommending the same model multiple times across different requests.\n"
            "- Make sure the response is always valid JSON. Do not include explanations outside the JSON.\n"
        )

        user_prompt = (
            f"User Requirement:\n"
            f"{analyzed_input.strip()}\n\n"
            f"Model Dataset:\n"
            f"{json.dumps(dataset)}\n\n"
            "Instructions:\n"
            "- Match user task(s) with model capabilities.\n"
            "- Prioritize accuracy, budget, speed, and task-fit.\n"
            "- Output format:\n"
            "[\n"
            "  {\n"
            "    \"Model Name\": \"<model name>\",\n"
            "    \"Reason\": \"<short reason for this task>\"\n"
            "  },\n"
            "  ... (up to 5 models)\n"
            "]"
        )

        # 🧠 Step 5: GPT Call
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

            try:
                recommendations = json.loads(result)
                if isinstance(recommendations, list):
                    logger.info("✅ Parsed GPT output successfully.")
                    return recommendations
                else:
                    logger.warning("⚠️ GPT output is not a list.")
                    return [{"message": "Unexpected format from GPT. Please retry."}]
            except json.JSONDecodeError as decode_err:
                logger.warning(f"⚠️ Failed to parse GPT response: {decode_err}")
                return [{"message": "Failed to parse model recommendations."}]

        except Exception as e:
            logger.error(f"❌ GPT error during model recommendation: {e}")
            return [{"message": "GPT model recommendation failed. Please try again later."}]
