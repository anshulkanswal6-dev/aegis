import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # try looking in parent dir
    load_dotenv(dotenv_path=Path("..") / ".env")
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

print("Listing models...")
with open("available_models.txt", "w", encoding="utf-8") as f:
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                line = f"- {m.name} ({m.display_name})\n"
                print(line, end="")
                f.write(line)
    except Exception as e:
        print(f"Error listing models: {e}")
        f.write(f"Error: {e}\n")
