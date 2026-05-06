# =========================================================
# llm_processor.py
# FINAL VERSION – OpenRouter + .env API Key
# Supports Text + Image (Multimodal)
# =========================================================

import os
import logging
import requests
from dotenv import load_dotenv


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env file")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def analyze_image_and_text(
    base64_image=None,
    user_text="",
    is_multimodal=False,
    mime_type=None,
    model_override=None
):


    model_name = model_override
    if not model_name:
        raise ValueError("model_override must be provided")

    try:

        content = [
            {
                "type": "text",
                "text": user_text
            }
        ]

        if is_multimodal and base64_image:
            if not mime_type:
                mime_type = "image/jpeg"

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Multi-UGV-System"
        }

        # -----------------------------
        # API CALL
        # -----------------------------
        response = requests.post(
            OPENROUTER_API_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        logging.error(f"LLM ERROR: {e}")
        return f"[LLM ERROR] {e}"
