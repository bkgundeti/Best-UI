import json
from openai import AzureOpenAI  # Or from openai import OpenAI if not using Azure
from agents.logger import get_logger

logger = get_logger("report_agent", "logs/report_agent.log")

class ReportAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client
        logger.info("✅ ReportAgent initialized with GPT client.")

    def is_valid_input(self, analyzed_input, recommended_models, pricing_table):
        if not analyzed_input or not recommended_models or not pricing_table:
            logger.warning("❌ Incomplete input. Skipping report generation.")
            return False
        if isinstance(recommended_models, list) and len(recommended_models) == 1:
            logger.info("🟡 Only 1 model recommended. ReportAgent may not be needed.")
            return False
        return True

    def generate_report(self, analyzed_input, recommended_models, pricing_table):
        # Step 1: Check if execution is necessary
        if not self.is_valid_input(analyzed_input, recommended_models, pricing_table):
            return "Skipping report generation. Input is not suitable or already narrowed to 1 model."

        logger.info("📩 Generating final report using GPT...")
        logger.debug(f"📝 Analyzed Input:\n{analyzed_input}")
        logger.debug(f"📊 Recommended Models:\n{json.dumps(recommended_models, indent=2)}")
        logger.debug(f"💰 Pricing Table:\n{json.dumps(pricing_table, indent=2)}")

        # Step 2: Prompt setup
        prompt = f"""
You are an expert AI model selector.

Step 1: Review the full context.

1. User Requirement:
\"\"\"{analyzed_input.strip()}\"\"\"

2. Recommended Models (from Recommender):
{json.dumps(recommended_models, indent=2)}

3. Pricing & Specs (from PricingAgent):
{json.dumps(pricing_table, indent=2)}

Step 2: Final Output Format (choose ONLY ONE best model):

Final Best Model Recommended:
1. Model Name      : <model_name>
2. Price           : <price with units>
3. Speed           : <descriptive speed>
4. Accuracy        : <percentage format like 97.6%>
5. Cloud           : <Cloud provider>
6. Region          : <deployment region>
7. Reason for Selection : <clear reason why this model is best>

Guidelines:
- Infer missing values (e.g., speed or accuracy) politely if not available.
- NEVER use “Not specified” or “Unknown”.
- Keep formatting consistent and aligned.
- Output must be professional text (no markdown, no emojis).
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a smart assistant generating final selection reports "
                            "based on AI model recommendations. Output should be clean, aligned, and accurate."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=800
            )

            result = response.choices[0].message.content.strip()

            logger.info("✅ Final model recommendation report generated successfully.")
            logger.debug(f"📄 Final Report:\n{result}")

            return result

        except Exception as e:
            logger.error(f"❌ Error generating final report: {repr(e)}")
            return "Sorry, something went wrong while generating the final model selection report."
