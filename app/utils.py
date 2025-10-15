# app/utils.py
import os
import uuid
from datetime import datetime
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("mistralai/Mixtral-8x7B-Instruct-v0.1")


def make_uuid():
    return uuid.uuid4().hex

def timestamp_now():
    return datetime.utcnow().isoformat() + "Z"

def ensure_sites_dir(path="./sites"):
    os.makedirs(path, exist_ok=True)
    return path

def count_tokens(text: str) -> int:
    """Підраховує кількість токенів у тексті."""
    if not text:
        return 0
    return len(tokenizer.encode(text))
