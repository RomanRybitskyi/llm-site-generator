from dotenv import load_dotenv
import os
from typing import Optional
from PIL import Image
from huggingface_hub import InferenceClient
from app.logger import logger
from app.utils import ensure_sites_dir

load_dotenv()
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"

SITES_DIR = ensure_sites_dir(os.getenv("SITES_DIR", "./sites"))

client = InferenceClient(model=MODEL, token=HF_TOKEN)
image_client = InferenceClient(model=IMAGE_MODEL, token=HF_TOKEN)

def inference(prompt: str, params: dict) -> dict:
    """Call Hugging Face API via current client."""
    try:
        messages = [{"role": "user", "content": prompt}]
        output = client.chat_completion(
            messages=messages,
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.9),
            max_tokens=params.get("max_new_tokens", 512)
        )
        result = output.choices[0].message.content
        logger.info(f"Inference successful, generated {len(result)} characters")
        return {"generated_text": result}
    except Exception as e:
        logger.error(f"Inference error: {str(e)}")
        return {"generated_text": ""}

def inference_image(prompt: str) -> Optional[Image.Image]:
    """Generate image via Hugging Face API."""
    try:
        response = image_client.text_to_image(
            prompt=prompt,
            negative_prompt="low quality, blurry, distorted, text, watermark",
            guidance_scale=7.5,
            num_inference_steps=30,
            height=512,
            width=512
        )
        logger.info(f"Image generated successfully for prompt: {prompt[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Image generation error for prompt '{prompt[:50]}...': {str(e)}")
        return None