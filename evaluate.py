# evaluate.py
import argparse
import os
import json
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
import numpy as np

SITES_DIR = os.getenv("SITES_DIR", "./sites")
MODEL_NAME = 'all-MiniLM-L6-v2' # Ефективна модель для семантичної схожості

def get_site_content(file_path: str) -> str:
    """Витягує текстовий контент з HTML-файлу."""
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        # Видаляємо непотрібні теги
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text(separator=" ", strip=True)

def main(site_files: list):
    """Обчислює та виводить семантичну схожість між сайтами."""
    if len(site_files) < 2:
        print("Error: Please provide at least two site files to compare.")
        return

    print(f"Loading sentence transformer model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    contents = []
    valid_files = []
    for file in site_files:
        path = os.path.join(SITES_DIR, file)
        content = get_site_content(path)
        if content:
            contents.append(content)
            valid_files.append(file)
        else:
            print(f"Warning: Could not read or find content for {file}")

    if len(contents) < 2:
        print("Not enough valid content to compare.")
        return

    print("Encoding site contents into vectors...")
    embeddings = model.encode(contents, convert_to_tensor=True)
    
    # Обчислюємо косинусну схожість між усіма парами
    cosine_scores = util.cos_sim(embeddings, embeddings)

    print("\n--- Semantic Similarity Matrix (1.0 = identical) ---")
    
    # Друк заголовків
    header = " " * 18 + " ".join([f"{name[:15]:>15}" for name in valid_files])
    print(header)
    print("-" * len(header))

    # Друк рядків матриці
    for i, file_name in enumerate(valid_files):
        row_str = f"{file_name[:15]:<15} |"
        for j in range(len(valid_files)):
            row_str += f" {cosine_scores[i][j]:.3f}{' ' * 10}"
        print(row_str)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate semantic similarity between generated sites.")
    parser.add_argument("site_files", nargs='+', help="List of site HTML filenames (e.g., site_abc.html site_xyz.html)")
    args = parser.parse_args()
    
    main(args.site_files)