from typing import Final, List, Dict, Any

from google import genai

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: Final = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = (
    """
    You are an AI-powered assistant designed to help Indian artisans and craftsmen market their products, 
    tell their stories, and expand their digital presence. Always provide friendly, practical, and culturally 
    sensitive advice. Help users create compelling product descriptions, marketing content, and answer questions 
    about selling online. Encourage and empower artisans to share their unique heritage with the world.

    Self Instruction: Keep your responses concise, clear, and under 4000 characters so they fit in Telegram messages. 
    Only provide longer, detailed responses if the user explicitly requests it.
    """
)

async def get_gemini_response(history: List[Dict[str, Any]]) -> str:
    """
    Send the full conversation history to Gemini and return the model's response.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
    )

    if not response.text:
        return "No response from Gemini API."
    
    return response.text