import os
import json
import docx
import csv
import pandas as pd
import pytesseract
import speech_recognition as sr
from PIL import Image
from agents.logger import get_logger

logger = get_logger("chat_agent", "logs/chat_agent.log")

class ChatAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client

    def _read_text_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return ""

    def _read_docx_file(self, file_path):
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error reading DOCX: {e}")
            return ""

    def _read_csv_file(self, file_path):
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                reader = csv.reader(f)
                return "\n".join([", ".join(row) for row in reader])
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return ""

    def _read_xlsx_file(self, file_path):
        try:
            df = pd.read_excel(file_path)
            return df.to_string(index=False)
        except Exception as e:
            logger.error(f"Error reading XLSX: {e}")
            return ""

    def _read_json_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.dumps(json.load(f), indent=2)
        except Exception as e:
            logger.error(f"Error reading JSON: {e}")
            return ""

    def _read_image_file(self, file_path):
        try:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return ""

    def _read_audio_file(self, file_path):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data)
        except Exception as e:
            logger.error(f"Error reading audio: {e}")
            return ""

    def _handle_file_input(self, file_path):
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == '.txt':
            return self._read_text_file(file_path)
        elif ext == '.docx':
            return self._read_docx_file(file_path)
        elif ext == '.csv':
            return self._read_csv_file(file_path)
        elif ext == '.xlsx':
            return self._read_xlsx_file(file_path)
        elif ext == '.json':
            return self._read_json_file(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self._read_image_file(file_path)
        elif ext in ['.mp3', '.wav']:
            return self._read_audio_file(file_path)
        else:
            logger.warning(f"Unsupported file format: {ext}")
            return ""

    def _collect_user_input(self):
        print("\nEnter your requirement (You can enter text or file path. Type 'exit' to quit):")
        lines = []
        while True:
            try:
                line = input("> ").strip()
            except Exception as e:
                logger.error(f"Input error: {e}")
                return ""

            if line.lower() in ["exit", "quit"]:
                return "EXIT_COMMAND"

            if line:
                lines.append(line)
            elif lines:
                break

        return "\n".join(lines).strip()

    def run_chat_loop(self):
        collected_input = ""

        while not collected_input:
            raw_input = self._collect_user_input()

            if raw_input == "EXIT_COMMAND":
                return "EXIT_COMMAND"

            for segment in raw_input.splitlines():
                segment = segment.strip()
                if os.path.exists(segment):
                    collected_input += "\n" + self._handle_file_input(segment)
                else:
                    collected_input += "\n" + segment

            if not collected_input.strip():
                print("No valid input detected. Please try again.")

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant that helps users ONLY with AI model recommendations.\n"
                        "If the user input is about using AI for tasks (like summarization, chatbot, detection, etc.), say:\n"
                        "'Thank you, I will now recommend an AI model.' and end with ##PROCEED##.\n\n"
                        "If the input is NOT about AI model recommendation (e.g. greetings, life advice, how to study), then:\n"
                        "- Politely respond with a DIFFERENT natural-sounding sentence depending on the input\n"
                        "- Example replies: 'That doesn't sound like a task for an AI model.' or 'Please describe the AI use-case you want help with.'\n"
                        "- Then end with this exact tag: ##HOLD##"
                    )
                },
                {
                    "role": "user",
                    "content": collected_input.strip()
                }
            ]
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            result = response.choices[0].message.content.strip()
            logger.info("Analysis result:\n" + result)

            if "##PROCEED##" in result:
                cleaned = result.replace("##PROCEED##", "").strip()
                return cleaned
            else:
                cleaned = result.replace("##HOLD##", "").strip()
                print(cleaned)
                return None

        except Exception as e:
            logger.error(f"GPT error: {repr(e)}")
            print(f"GPT failed to analyze input. Error: {repr(e)}")
            return None

    def process_web_input(self, user_input):
        try:
            if not user_input or not user_input.strip():
                return {
                    "proceed": False,
                    "message": "Input is empty. Please provide a requirement."
                }

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent assistant focused ONLY on recommending AI models.\n"
                        "If the user input is about using AI for tasks like summarization, text generation, image recognition, etc., "
                        "respond with: 'Great, I will now suggest the most suitable AI models for your case.' and end with ##PROCEED##.\n\n"
                        "If it's NOT a valid model use-case (e.g. hello, exam question, how are you), reply naturally and POLITELY "
                        "with varied wording depending on the input.\n"
                        "Do NOT repeat the same sentence. Be helpful but end by saying: 'Please ask something model-related so I can assist.' and then add ##HOLD##."
                    )
                },
                {
                    "role": "user",
                    "content": user_input.strip()
                }
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )

            result = response.choices[0].message.content.strip()
            logger.info("Web input analysis result:\n" + result)

            if "##PROCEED##" in result:
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
