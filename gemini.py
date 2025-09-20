from typing import Final, List, Dict, TypedDict, Any

from google import genai

import os
import json
from dotenv import load_dotenv

from tools import FUNCTION_DECLARATIONS

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

class Caption(TypedDict):
    text: str
    hashtags: List[str]
    emojis: List[str]

class CaptionResponse(TypedDict):
    captions: List[Caption]
    error: str | None


async def generate_marketing_captions(image_path: str, description: str) -> CaptionResponse:
    """
    Generate 3 marketing captions using Gemini with structured output.
    """
    prompt = f"""
    Generate 3 marketing captions for the following product:
    
    Image Path: {image_path}
    Description: {description}
    
    Requirements:
    - Each caption should be engaging and social media friendly
    - Include relevant hashtags for Indian artisans and crafts
    - Include appropriate emojis
    - Keep the main text within 200 characters
    - Highlight unique selling points
    
    Format your response as a JSON object matching this schema:
    {json.dumps(FUNCTION_DECLARATIONS["generate_marketing_captions"]["parameters"], indent=2)}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
        )

        if not response.text:
            return {"captions": [], "error": "No response from Gemini API"}

        # Extract JSON from response
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:-3]  # Remove ```json and ``` markers
        
        result = json.loads(json_str)
        return {"captions": result["captions"], "error": None}

    except Exception as e:
        return {"captions": [], "error": f"Error generating captions: {str(e)}"}