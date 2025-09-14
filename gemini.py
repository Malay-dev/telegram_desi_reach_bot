from typing import Final

from google import genai

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: Final = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

async def get_gemini_response(content: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=content,
    )

    if response.text is None:
        return "No response from Gemini API."
    
    return response.text
