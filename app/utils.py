# app/utils.py
import os
import uuid
from datetime import datetime

def make_uuid():
    return uuid.uuid4().hex

def timestamp_now():
    return datetime.utcnow().isoformat() + "Z"

def ensure_sites_dir(path="./sites"):
    os.makedirs(path, exist_ok=True)
    return path
