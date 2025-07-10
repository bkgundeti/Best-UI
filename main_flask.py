# main_flask.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from werkzeug.utils import secure_filename

from agents.chat_agent import ChatAgent
from agents.requir_recommender_agent import RecommenderAgent
from agents.pricing_agent import PricingAgent
from agents.report_agent import ReportAgent

# ✅ Load .env variables
load_dotenv()

app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
CORS(app)

# ✅ MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI")
user_db_name = os.getenv("USER_DB_NAME")               # AI_model_selector
users_collection_name = os.getenv("USERS_COLLECTION_NAME")  # users
chats_collection_name = os.getenv("CHATS_COLLECTION_NAME")  # chats

mongo_client = MongoClient(mongo_uri)
user_db = mongo_client[user_db_name]
users_col = user_db[users_collection_name]
chats_col = user_db[chats_collection_name]

# ✅ Azure OpenAI Setup
gpt_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    default_headers={"azure-openai-deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")}
)
assistant_id = os.getenv("AZURE_OPENAI_ASSISTANT_ID")

# ✅ Login API
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify({"status": "fail", "message": "User not found"}), 404
    if user["password"] != password:
        return jsonify({"status": "fail", "message": "Incorrect password"}), 401

    return jsonify({"status": "success"})

# ✅ Chat API
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    username = data.get("username")
    message = data.get("message")

    chat_agent = ChatAgent(gpt_client)
    chat_response = chat_agent.process_web_input(message)

    if not chat_response or not chat_response["proceed"]:
        response = chat_response["message"] if chat_response else "Could not process."
    else:
        analyzed_input = chat_response["message"]
        recommender = RecommenderAgent(gpt_client)
        recommended = recommender.recommend_models(analyzed_input)

        pricing = PricingAgent(
            assistant_id,
            os.getenv("AZURE_OPENAI_KEY"),
            os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        pricing_table = pricing.analyze_pricing(recommended)

        reporter = ReportAgent(gpt_client)
        response = reporter.generate_report(analyzed_input, recommended, pricing_table)

    chats_col.insert_one({"username": username, "message": message, "response": response})
    return jsonify({"response": response})

# ✅ Chat History API
@app.route("/history/<username>", methods=["GET"])
def history(username):
    chats = chats_col.find({"username": username})
    return jsonify([
        {"username": username, "message": c["message"]} if i % 2 == 0 else {"username": "Agent", "message": c["response"]}
        for i, c in enumerate(chats)
    ])

# ✅ File Upload API
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(filepath)
        return jsonify({"status": "success", "file": filename})
    return jsonify({"status": "fail"}), 400

# ✅ Clear Chat API
@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    username = request.get_json().get("username")
    chats_col.delete_many({"username": username})
    return jsonify({"status": "cleared"})

# ✅ Serve Frontend React App
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

# ✅ Run Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
