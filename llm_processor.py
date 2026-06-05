# =========================================================
# llm_processor.py
# OpenRouter + Debug Version
# Supports Text + Image (Multimodal)
# =========================================================

import os
import logging
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env file")

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)

# ---------------------------------------------------------
# OPENROUTER ENDPOINT
# ---------------------------------------------------------
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ---------------------------------------------------------
# MAIN LLM FUNCTION
# ---------------------------------------------------------
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

        # -------------------------------------------------
        # BUILD CONTENT
        # -------------------------------------------------
        content = [
            {
                "type": "text",
                "text": user_text
            }
        ]

        # -------------------------------------------------
        # IMAGE INPUT
        # -------------------------------------------------
        if is_multimodal and base64_image:

            if not mime_type:
                mime_type = "image/jpeg"

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            )

        # -------------------------------------------------
        # PAYLOAD
        # -------------------------------------------------
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

        # -------------------------------------------------
        # HEADERS
        # -------------------------------------------------
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Multi-UGV-System"
        }

        # -------------------------------------------------
        # DEBUG INFO
        # -------------------------------------------------
        logging.info("=" * 60)
        logging.info("OPENROUTER REQUEST")
        logging.info(f"MODEL           : {model_name}")
        logging.info(f"MULTIMODAL      : {is_multimodal}")
        logging.info(f"MIME TYPE       : {mime_type}")
        logging.info(f"TEXT LENGTH     : {len(user_text)}")

        if base64_image:
            logging.info(
                f"IMAGE SIZE(B64) : {len(base64_image):,} chars"
            )

        logging.info("=" * 60)

        # -------------------------------------------------
        # API CALL
        # -------------------------------------------------
        response = requests.post(
            OPENROUTER_API_URL,
            json=payload,
            headers=headers,
            timeout=120
        )

        # -------------------------------------------------
        # PRINT RAW RESPONSE
        # -------------------------------------------------
        print("\n")
        print("=" * 70)
        print("OPENROUTER DEBUG")
        print("=" * 70)
        print("MODEL:")
        print(model_name)
        print("-" * 70)
        print("STATUS:")
        print(response.status_code)
        print("-" * 70)
        print("BODY:")
        print(response.text)
        print("=" * 70)
        print("\n")

        # -------------------------------------------------
        # CHECK ERRORS
        # -------------------------------------------------
        response.raise_for_status()

        data = response.json()

        if (
            "choices" not in data
            or len(data["choices"]) == 0
        ):
            raise RuntimeError(
                f"Unexpected response:\n{data}"
            )

        return data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP ERROR: {e}")
        return f"[LLM HTTP ERROR] {e}"

    except requests.exceptions.RequestException as e:
        logging.error(f"REQUEST ERROR: {e}")
        return f"[LLM REQUEST ERROR] {e}"

    except Exception as e:
        logging.error(f"LLM ERROR: {e}")
        return f"[LLM ERROR] {e}"