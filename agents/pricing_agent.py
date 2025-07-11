import time
from openai import AzureOpenAI
from agents.logger import get_logger

logger = get_logger("pricing_agent", "logs/pricing_agent.log")

class PricingAgent:
    def __init__(self, assistant_id, azure_api_key, azure_endpoint, api_version="2024-05-01-preview"):
        logger.info("✅ Initializing PricingAgent...")
        self.assistant_id = assistant_id
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )

    def analyze_pricing(self, model_list):
        logger.info("===== Step 3: Pricing Analysis Started =====")
        logger.info("Received model shortlist for pricing:")
        for model in model_list:
            logger.info(f"   - {model}")

        # Build GPT prompt for assistant
        prompt = (
            "You are a pricing analyst AI. Your task is to analyze and estimate pricing info for ONLY the models listed below.\n\n"
            "For each model, use either:\n"
            "1. Pricing from uploaded file (if available)\n"
            "2. Your trusted internal knowledge base (latest known prices as of 2024)\n\n"
            "You must always return accurate pricing for all of the following fields:\n"
            "- Estimated Price (in $)\n"
            "- Price Unit (per 1k tokens, image, etc.)\n"
            "- Provider (like OpenAI, Google, Anthropic, Mistral, etc.)\n"
            "- Region (e.g. Global, US, EU, India, etc.)\n\n"
            "If info is absolutely missing, use 'Estimated', 'Likely', or 'Not Public' instead of 'Unknown'.\n\n"
            "Respond with ONLY a markdown table in this format:\n"
            "| Model | Estimated Price | Price Unit | Provider | Region |\n"
            "|-------|------------------|------------|----------|--------|\n\n"
            "Models to analyze:\n" +
            "\n".join(f"- {model}" for model in model_list)
        )

        logger.info("📝 Prepared prompt for assistant:\n" + prompt)

        # Create assistant thread
        thread = self.client.beta.threads.create()
        logger.info(f"🧵 Created assistant thread ID: {thread.id}")

        # Send message
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        logger.info("📤 Sent prompt to assistant.")

        # Run assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        logger.info(f"🏃 Assistant run started. Run ID: {run.id}")

        # Poll for completion
        logger.info("⏳ Waiting for assistant to finish...")
        while run.status not in ["completed", "failed"]:
            time.sleep(2)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        # Failure check
        if run.status == "failed":
            logger.error("❌ Assistant run failed.")
            return "Assistant failed to analyze pricing."

        # Get assistant's reply
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        response = ""
        for msg in messages.data:
            if msg.role == "assistant":
                response += msg.content[0].text.value

        logger.info("✅ Assistant Pricing Table Response:\n" + response)
        return response
