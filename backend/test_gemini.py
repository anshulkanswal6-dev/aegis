import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"Testing API Key: {api_key[:10]}...")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    response = model.generate_content('Hi Aegis, are you there and ready to generate some onchain automations?')
    print("\n--- AI RESPONSE ---")
    print(response.text)
    print("-------------------\n")
    print("SUCCESS: Gemini 2.5 Flash is responsive.")
except Exception as e:
    print(f"FAILURE: {str(e)}")
