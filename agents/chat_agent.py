import os
import json
import docx
import csv
import pandas as pd
import pytesseract
import speech_recognition as sr
from PIL import Image
import PyPDF2
from agents.logger import get_logger

logger = get_logger("chat_agent", "logs/chat_agent.log")


class ChatAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client
        self.selected_model_info = None
        self.last_user_task = None

    def set_selected_model(self, model_info):
        self.selected_model_info = model_info

    def set_last_user_task(self, task):
        self.last_user_task = task

    def handle_follow_up(self, user_input):
        """Respond to follow-up question about previously recommended model."""
        if not self.selected_model_info or not self.last_user_task:
            return "No model has been selected yet or original task is missing."

        system_prompt = (
            "You are an AI assistant that previously recommended a model to the user for a specific task.\n"
            f"User Task: {self.last_user_task}\n\n"
            f"Recommended Model:\n{json.dumps(self.selected_model_info, indent=2)}\n\n"
            "Now the user is asking a follow-up question. Respond strictly based on the model above.\n"
            "- If the user asks about pricing (e.g. cost per image), extract the relevant part from the model pricing.\n"
            "- If the user asks about availability or region (e.g. India), use the 'Region' field.\n"
            "- Be specific, concise, and informative. Do not say you can't help.\n"
            "- Do not repeat all model details again.\n"
            "User follow-up:\n"
            f"{user_input.strip()}"
        )

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input.strip()}
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Follow-up error: {e}")
            return "Sorry, I couldn’t answer your follow-up right now."

    # ===== File Readers =====
    def _read_text_file(self, path):
        try:
            with open(path, 'r', encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Text read error: {e}")
            return ""

    def _read_docx_file(self, path):
        try:
            doc = docx.Document(path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX read error: {e}")
            return ""

    def _read_pdf_file(self, path):
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        except Exception as e:
            logger.error(f"PDF read error: {e}")
            return ""

    def _read_csv_file(self, path):
        try:
            with open(path, 'r', encoding="utf-8") as f:
                reader = csv.reader(f)
                return "\n".join([", ".join(row) for row in reader])
        except Exception as e:
            logger.error(f"CSV read error: {e}")
            return ""

    def _read_xlsx_file(self, path):
        try:
            df = pd.read_excel(path)
            return df.to_string(index=False)
        except Exception as e:
            logger.error(f"XLSX read error: {e}")
            return ""

    def _read_json_file(self, path):
        try:
            with open(path, 'r') as f:
                return json.dumps(json.load(f), indent=2)
        except Exception as e:
            logger.error(f"JSON read error: {e}")
            return ""

    def _read_image_file(self, path):
        try:
            img = Image.open(path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            return ""

    def _read_audio_file(self, path):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(path) as source:
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data)
        except Exception as e:
            logger.error(f"Audio read error: {e}")
            return ""

    def _read_file_content(self, file_path):
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == '.txt':
            return self._read_text_file(file_path)
        elif ext == '.docx':
            return self._read_docx_file(file_path)
        elif ext == '.pdf':
            return self._read_pdf_file(file_path)
        elif ext == '.csv':
            return self._read_csv_file(file_path)
        elif ext == '.xlsx':
            return self._read_xlsx_file(file_path)
        elif ext == '.json':
            return self._read_json_file(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self._read_image_file(file_path)
        elif ext in ['.wav', '.mp3']:
            return self._read_audio_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return ""

    # ===== Main Input Processor =====
    def process_web_input(self, user_input):
        try:
            if not user_input or not user_input.strip():
                return {
                    "proceed": False,
                    "message": "Input is empty. Please provide a requirement."
                }

            # ✅ Detect if it's a follow-up question (by keywords)
            if self.selected_model_info and self.last_user_task:
                followup_keywords = [
                    "price", "cost", "token", "speed", "accuracy", "available",
                    "region", "country", "image", "input", "output", "how much", "is it"
                ]
                lower_msg = user_input.lower()
                if any(kw in lower_msg for kw in followup_keywords):
                    followup = self.handle_follow_up(user_input)
                    return {
                        "proceed": True,
                        "message": followup
                    }

            # Collect full content (text + files)
            collected = ""
            for line in user_input.strip().splitlines():
                line = line.strip()
                if os.path.exists(line):
                    content = self._read_file_content(line)
                    collected += f"\n{content}"
                else:
                    collected += f"\n{line}"

            if not collected.strip():
                return {
                    "proceed": False,
                    "message": "No valid input found in text or files."
                }

            # Ask GPT if it's a valid AI task
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent assistant focused ONLY on recommending AI models.\n"
                        "If the user input is about using AI for tasks like summarization, generation, image creation, speech transcription, etc., "
                        "respond with: 'Great, I will now suggest the most suitable AI models for your case.' and end with ##PROCEED##.\n\n"
                        "If it's not valid for model recommendation (e.g. greetings, jokes), reply politely and end with ##HOLD##."
                    )
                },
                {"role": "user", "content": collected.strip()}
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )

            result = response.choices[0].message.content.strip()
            logger.info("Web input analysis result:\n" + result)

            if "##PROCEED##" in result:
                self.set_last_user_task(user_input.strip())  # Save original task
                return {
                    "proceed": True,
                    "message": result.replace("##PROCEED##", "").strip()
                }
            else:
                return {
                    "proceed": False,
                    "message": result.replace("##HOLD##", "").strip()
                }

        except Exception as e:
            logger.error(f"Web GPT error: {repr(e)}")
            return {
                "proceed": False,
                "message": "Something went wrong while analyzing your input."
            }
