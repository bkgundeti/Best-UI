from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from werkzeug.utils import secure_filename
from datetime import datetime
import re

from agents.chat_agent import ChatAgent
from agents.requir_recommender_agent import RecommenderAgent
from agents.pricing_agent import PricingAgent
from agents.report_agent import ReportAgent

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
CORS(app)

# ✅ MongoDB Setup
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
user_db = mongo_client[os.getenv("USER_DB_NAME")]
users_col = user_db[os.getenv("USERS_COLLECTION_NAME")]
chats_col = user_db[os.getenv("CHATS_COLLECTION_NAME")]

# ✅ Azure OpenAI Client Setup
gpt_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    default_headers={"azure-openai-deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")}
)
assistant_id = os.getenv("AZURE_OPENAI_ASSISTANT_ID")

# ✅ Global Agent
chat_agent = ChatAgent(gpt_client)

# ✅ Lock per user to prevent multiple parallel requests
user_processing_lock = {}

# ✅ Sign Up API
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if users_col.find_one({"username": username}):
        return jsonify({"success": False, "message": "Username already exists"}), 409

    if users_col.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email already registered"}), 409

    users_col.insert_one({
        "username": username,
        "email": email,
        "password": password,
        "created_at": datetime.utcnow()
    })

    return jsonify({"success": True, "message": "Account created"}), 201

# ✅ Login API
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    if user["password"] != password:
        return jsonify({"success": False, "message": "Incorrect password"}), 401

    return jsonify({"success": True, "message": "Login successful"}), 200

# ✅ Chat API 
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    username = data.get("username")
    message = data.get("message")

    if not username or not message:
        return jsonify({"response": "Missing username or message"}), 400

    if user_processing_lock.get(username, False):
        return jsonify({"response": "Please wait, your previous request is still being processed."}), 429

    user_processing_lock[username] = True

    try:
        # Step 1: Handle follow-up questions if model is selected
        if chat_agent.selected_model_info:
            followup_response = chat_agent.handle_follow_up(message)
            chats_col.insert_one({
                "username": username,
                "message": message,
                "response": followup_response,
                "timestamp": datetime.utcnow()
            })
            return jsonify({"response": followup_response}), 200

        # Step 2: Use Chat Agent for message analysis
        chat_response = chat_agent.process_web_input(message)

        # Step 3: If ChatAgent is confident and provides useful response
        if not chat_response or not chat_response.get("proceed") or chat_response.get("mode") not in ["new_request", "alternative"]:
            response = chat_response.get("message", "Sorry, I couldn't understand your input.")
            chats_col.insert_one({
                "username": username,
                "message": message,
                "response": response,
                "timestamp": datetime.utcnow()
            })
            return jsonify({"response": response}), 200

        # Step 4: Use RecommenderAgent for model suggestions
        analyzed_input = chat_response["message"]
        recommender = RecommenderAgent(gpt_client)
        recommended = recommender.recommend_models(
            analyzed_input,
            alternative_mode=(chat_response["mode"] == "alternative"),
            exclude_model_name=chat_agent.selected_model_info.get("Model_name") if chat_agent.selected_model_info else None
        )

        if not recommended or not isinstance(recommended, list):
            return jsonify({"response": "Failed to get model recommendations."}), 500

        # Step 5: Pricing Analysis
        pricing_agent = PricingAgent(
            assistant_id,
            os.getenv("AZURE_OPENAI_KEY"),
            os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        pricing_table = pricing_agent.analyze_pricing(recommended)

        # Step 6: Report Generation
        reporter = ReportAgent(gpt_client)
        final_output = reporter.generate_report(analyzed_input, recommended, pricing_table)

        # Step 7: Save selected model for follow-ups
        try:
            model_name_match = re.search(r"Model Name\s*:\s*(.+)", final_output)
            if model_name_match:
                selected_name = model_name_match.group(1).strip()
                all_models = recommender._fetch_model_dataset()
                matched = next((m for m in all_models if m.get("Model_name") == selected_name), None)
                if matched:
                    chat_agent.set_selected_model(matched)
        except Exception as err:
            print("⚠️ Model extraction failed:", err)

        chats_col.insert_one({
            "username": username,
            "message": message,
            "response": final_output,
            "timestamp": datetime.utcnow()
        })

        return jsonify({"response": final_output}), 200

    finally:
        user_processing_lock[username] = False

# ✅ Chat History
@app.route("/history/<username>", methods=["GET"])
def history(username):
    if not username:
        return jsonify([])

    chats = chats_col.find({"username": username})
    return jsonify([
        {"username": username, "message": c["message"]} if i % 2 == 0 else {"username": "Agent", "message": c["response"]}
        for i, c in enumerate(chats)
    ])

# ✅ File Upload
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"status": "fail", "message": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    return jsonify({"status": "success", "message": f"{filename} uploaded successfully"}), 200

# ✅ Clear Chat + Reset
@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"status": "fail", "message": "Missing username"}), 400

    chats_col.delete_many({"username": username})
    chat_agent.selected_model_info = None
    return jsonify({"status": "cleared"}), 200

# ✅ React Frontend Support
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    file_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ✅ Start Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
