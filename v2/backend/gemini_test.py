import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables (API key)
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Add it to your .env file.")

# Initialize the new-style client
client = genai.Client(api_key=api_key)

MODEL = "gemini-3-flash-preview"


def test_simple_prompt():
    """Test a simple prompt with the model"""
    try:
        print("\n===== Simple Prompt Response =====")
        response = client.models.generate_content(
            model=MODEL,
            contents="What are the top 3 symptoms of plant rust disease?",
        )
        print(response.text)
        print("=================================\n")
        return True
    except Exception as e:
        print(f"Simple prompt test failed: {e}")
        return False


def test_chat():
    """Test multi-turn chat using the new SDK"""
    try:
        print("\n===== Chat Test =====")

        # Build a two-turn conversation manually
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="How do I identify rust in my mango plant?")],
            ),
        ]

        response1 = client.models.generate_content(model=MODEL, contents=contents)
        answer1 = response1.text
        print("Q: How do I identify rust in my mango plant?")
        print(f"A: {answer1}")

        # Append model reply + follow-up question for context
        contents.append(
            types.Content(role="model", parts=[types.Part.from_text(text=answer1)])
        )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="What fungicides can I use to treat it?")],
            )
        )

        time.sleep(1)  # Small delay to avoid rate limits
        response2 = client.models.generate_content(model=MODEL, contents=contents)
        print("\nQ: What fungicides can I use to treat it?")
        print(f"A: {response2.text}")
        print("======================\n")
        return True
    except Exception as e:
        print(f"Chat test failed: {e}")
        return False


def test_structured_output():
    """Test getting structured output from the model"""
    try:
        prompt = """
        Create a JSON object with information about rust disease in plants.
        Include:
        - Name of disease
        - Common symptoms (at least 3)
        - Treatment methods (at least 3)
        - Preventive measures (at least 3)
        """

        response = client.models.generate_content(model=MODEL, contents=prompt)

        print("\n===== Structured Output Test =====")
        print(response.text)
        print("==================================\n")
        return True
    except Exception as e:
        print(f"Structured output test failed: {e}")
        return False


def test_streaming():
    """Test streaming response"""
    try:
        print("\n===== Streaming Test =====")
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents="Give me 3 quick tips on organic farming.",
        ):
            print(chunk.text, end="", flush=True)
        print("\n==========================\n")
        return True
    except Exception as e:
        print(f"Streaming test failed: {e}")
        return False


def main():
    """Run all tests and report results"""
    print(f"GEMINI API TEST  |  Model: {MODEL}\n")

    simple_test = test_simple_prompt()
    chat_test = test_chat()
    structured_test = test_structured_output()
    streaming_test = test_streaming()

    print("\n===== TEST SUMMARY =====")
    print(f"Simple prompt test:    {'PASSED' if simple_test else 'FAILED'}")
    print(f"Chat test:             {'PASSED' if chat_test else 'FAILED'}")
    print(f"Structured output test:{'PASSED' if structured_test else 'FAILED'}")
    print(f"Streaming test:        {'PASSED' if streaming_test else 'FAILED'}")
    print("========================\n")

    if all([simple_test, chat_test, structured_test, streaming_test]):
        print("All tests passed! Gemini API is working correctly.")
    else:
        print("Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()