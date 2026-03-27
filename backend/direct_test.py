import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".") / ".env")
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model_name = "models/gemini-flash-latest"
print(f"Testing model: {model_name}")

try:
    m = genai.GenerativeModel(model_name)
    response = m.generate_content("Say hello")
    print(f"Response: {response.text}")
    print("✅ SUCCESS: Model is working.")
except Exception as e:
    print(f"❌ FAILED: {e}")
