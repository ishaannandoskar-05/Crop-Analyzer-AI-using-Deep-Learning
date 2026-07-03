import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found.")
else:
    genai.configure(api_key=api_key)
    print(f"Checking models for API key ending in ...{api_key[-5:]}")
    try:
        models = list(genai.list_models())
        print(f"Total models found: {len(models)}")
        for m in models:
            print(f"Model: {m.name} | Methods: {m.supported_generation_methods}")
    except Exception as e:
        print(f"Error: {e}")
