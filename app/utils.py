# app/utils.py
import os
import uuid
from datetime import datetime
from transformers import AutoTokenizer
from bs4 import BeautifulSoup

tokenizer = AutoTokenizer.from_pretrained("mistralai/Mixtral-8x7B-Instruct-v0.1")


def make_uuid():
    return uuid.uuid4().hex

def timestamp_now():
    return datetime.utcnow().isoformat() + "Z"

def ensure_sites_dir(path="./sites"):
    os.makedirs(path, exist_ok=True)
    return path

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(tokenizer.encode(text))

def get_site_content_from_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text(separator=" ", strip=True)