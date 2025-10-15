# app/generator.py
from datetime import datetime
import os
import json
import logging
import random
import re
from typing import Optional
from PIL import Image
from jinja2 import Environment, FileSystemLoader

# Оновлені імпорти
from app.chains import get_planning_components, get_writing_components, llm
from app.prompts import choose_sections, prepare_writing_inputs
from app.utils import make_uuid, timestamp_now, ensure_sites_dir

# ... (Налаштування logging та інші константи залишаються без змін) ...
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SITES_DIR = ensure_sites_dir(os.getenv("SITES_DIR", "./sites"))
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"

from huggingface_hub import InferenceClient
image_client = InferenceClient(model=IMAGE_MODEL, token=HF_TOKEN)

def inference_image(prompt: str) -> Optional[Image.Image]:
    try:
        response = image_client.text_to_image(prompt=prompt, negative_prompt="low quality, blurry, text", height=512, width=512)
        logger.info(f"Image generated for prompt: {prompt[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")
        return None

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))


class SiteGenerator:
    def __init__(self):
        self.logs = []
        # Ініціалізуємо компоненти ланцюжків один раз
        self.planning_prompt, self.json_parser = get_planning_components()
        self.writing_prompt, self.string_parser = get_writing_components()
        logger.info("SiteGenerator initialized with LangChain components")

    async def generate_sites(self, req):
        # Цей метод залишається без змін
        logger.info(f"Starting generation: {req.pages_count} pages about '{req.topic}' in {req.style} style")
        results = []
        for i in range(req.pages_count):
            logger.info(f"Generating page {i+1}/{req.pages_count}")
            item = await self.generate_one_site(req)
            if item is None: # Обробка можливої помилки
                continue
            results.append(item)
        
        self.logs.append({"topic": req.topic, "count": req.pages_count, "style": req.style, "time": timestamp_now()})
        logger.info(f"Generation completed: {len(results)} pages created")
        return results

    async def generate_one_site(self, req):
        # 1) ВИЗНАЧЕННЯ ТЕМПЕРАТУРИ (без змін)
        if req.randomize_temperature:
            actual_temp = random.uniform(req.temperature_min, req.temperature_max)
        else:
            variation = req.temperature * 0.1
            actual_temp = max(0.1, min(1.5, req.temperature + random.uniform(-variation, variation)))
        logger.info(f"🌡️ Using temperature: {actual_temp:.2f}")

        # 2) ПЛАНУВАННЯ СТРУКТУРИ - **НОВА ЛОГІКА**
        try:
            sections = choose_sections()
            sections_str = json.dumps([s for s in sections])

            # Створюємо налаштовану модель "на льоту"
            configured_llm = llm.bind(temperature=actual_temp, top_p=req.top_p)
            
            # Збираємо повний ланцюжок прямо тут
            plan_chain = self.planning_prompt | configured_llm | self.json_parser
            
            plan_json = await plan_chain.ainvoke({
                "topic": req.topic, 
                "style": req.style,
                "sections_str": sections_str
            })
            plan_json["title"] = self._ensure_unique_title(plan_json.get("title", f"{req.topic} Guide"))
            logger.info(f"Plan generated successfully: {plan_json.get('title')}")
        except Exception as e:
            logger.error(f"LangChain planning failed: {e}. Using fallback structure.")
            plan_json = self._fallback_plan(req.topic)
        
        # 3) ГЕНЕРАЦІЯ ЗОБРАЖЕННЯ (без змін)
        site_id = make_uuid()
        image_path = self._generate_and_save_image(plan_json, req.topic, site_id) if req.generate_image else None

        # 4) ГЕНЕРАЦІЯ КОНТЕНТУ - **НОВА ЛОГІКА**
        writing_inputs = prepare_writing_inputs(
            req.topic, req.style, plan_json.get("title", ""), plan_json.get("sections", [])
        )
        
        # Створюємо налаштовану модель для написання
        configured_writer_llm = llm.bind(temperature=actual_temp, top_p=req.top_p, max_tokens=req.max_tokens)
        
        # Збираємо ланцюжок для написання
        write_chain = self.writing_prompt | configured_writer_llm | self.string_parser
        
        full_text = await write_chain.ainvoke(writing_inputs)
        
        generated_sections = self._extract_sections(full_text, plan_json.get("sections", []))

        # 5) РЕНДЕРИНГ ТА ЗБЕРЕЖЕННЯ (без змін)
        html = self._render_html(plan_json, generated_sections, image_path, req.style, req.topic)
        file_path = os.path.join(SITES_DIR, f"site_{site_id}.html")
        with open(file_path, "w", encoding="utf-8") as f: f.write(html)
        logger.info(f"Site saved: {file_path}")

        # 6) ЗАПИС У ЛОГ (без змін)
        record = {
            "site_id": site_id, "title": plan_json.get("title"), "meta_description": plan_json.get("meta_description"),
            "image_path": image_path, "file_path": file_path, "style": req.style, "sections_count": len(generated_sections),
            "temperature_used": round(actual_temp, 2), "created_at": timestamp_now()
        }
        self.logs.append(record)
        return record

    # ... (усі інші методи: _fallback_plan, _ensure_unique_title і т.д. залишаються без змін) ...
    def _fallback_plan(self, topic: str) -> dict:
        return {"title": f"{topic} — Comprehensive Guide", "meta_description": f"Discover everything about {topic}.", "image_prompt": f"Professional illustration representing {topic}", "sections": [{"heading": "Introduction", "brief": f"Overview of {topic}"}, {"heading": "Key Features", "brief": f"Main aspects of {topic}"}, {"heading": "Summary", "brief": f"Conclusions about {topic}"}]}
    def _ensure_unique_title(self, title: str) -> str:
        used_titles = {log.get("title") for log in self.logs if log.get("title")}
        original_title = title
        while title in used_titles: title = f"{original_title} ({make_uuid()[:6]})"
        return title
    def _generate_and_save_image(self, plan_json: dict, topic: str, site_id: str) -> Optional[str]:
        image_prompt = plan_json.get("image_prompt", f"Professional illustration of {topic}")
        image = inference_image(image_prompt)
        if image:
            image_path = f"image_{site_id}.png"
            abs_image_path = os.path.join(SITES_DIR, image_path)
            image.save(abs_image_path)
            logger.info(f"Image saved: {abs_image_path}")
            return image_path
        return None
    def _extract_sections(self, full_text: str, sections_data: list) -> list:
        parts = re.split(r'###\s*', full_text.strip())
        content_map = {}
        for part in parts:
            if '\n' in part:
                heading, content = part.split('\n', 1)
                content_map[heading.strip()] = content.strip()
        
        generated_sections = []
        for s_data in sections_data:
            heading = s_data.get("heading")
            content = content_map.get(heading, s_data.get("brief", f"Content for {heading} not found."))
            if content == s_data.get("brief"): logger.warning(f"Using fallback for section: {heading}")
            generated_sections.append({"heading": heading, "content": content})
        return generated_sections
    def _render_html(self, plan_json: dict, sections: list, image_path: Optional[str], style: str, topic: str) -> str:
        template_map = {"educational": "educational.html", "marketing": "marketing.html", "technical": "technical.html", "minimalist": "minimalist.html", "creative": "creative.html", "casual": "base.html"}
        template_name = template_map.get(style.lower(), "educational.html")
        image_url = f"/image/{image_path}" if image_path else None
        tpl = env.get_template(template_name)
        return tpl.render(title=plan_json.get("title", "Untitled"), meta_description=plan_json.get("meta_description", f"Learn about {topic}"), sections=sections, image_path=image_url, generated_at=datetime.utcnow().isoformat() + "Z")
    def get_site_path(self, site_id: str) -> Optional[str]:
        for r in self.logs:
            if r.get("site_id") == site_id: return r.get("file_path")
        return None
    def get_logs(self) -> list:
        return self.logs