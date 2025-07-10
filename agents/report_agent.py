import json
from openai import AzureOpenAI  # or from openai import OpenAI if not using Azure
from agents.logger import get_logger

logger = get_logger("report_agent", "logs/report_agent.log")

class ReportAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client
        logger.info("Report Agent initialized using GPT directly (no assistant)")

    def generate_report(self, analyzed_input, recommended_models, pricing_table):
        logger.info("Sending all inputs to GPT for final analysis...")

        prompt = f"""
You are an expert AI model selector.

Step 1: Below is the information provided by user and system:

1. Analyzed user requirement:
\"\"\"{analyzed_input}\"\"\"

2. Recommended models:
\"\"\"{recommended_models}\"\"\"

3. Pricing details of shortlisted models:
\"\"\"{pricing_table}\"\"\"

Step 2: Your task is to select the best model using logic.

Output Format (strictly follow this format):

Final Best Model Recommended:
1. Model Name      : <model_name>
2. Price           : <price with unit>
3. Speed           : <speed - always write something, even if approximate or inferred>
4. Accuracy        : <convert to percentage if decimal (e.g., 0.987 → 98.7 %)>
5. Cloud           : <cloud provider>
6. Region          : <region or deployment area>
7. Reason for Selection : <Short one-liner reason showing why this model fits best>

Rules:
- NEVER write "Not specified" for Speed or Accuracy.
- If Speed or Accuracy is missing, use best assumption or guess based on other fields.
- Format should be beautiful and consistent, no markdown, no bullets, no emojis.
- Maintain equal spacing after colons for clean readability.
- The reason must be short and clearly reflect accuracy/speed/user goal.
"""

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a smart assistant helping select the best AI model "
                            "with a professional, plain-text report. Ensure speed is filled, "
                            "accuracy is shown as %, and output is beautifully aligned."
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

            result = completion.choices[0].message.content.strip()
            logger.info("GPT response generated successfully.")
            return result

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"
