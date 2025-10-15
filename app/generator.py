# app/generator.py
from datetime import datetime
import os
import json
import logging
from typing import List, Optional
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from jinja2 import Environment, FileSystemLoader
from app.prompts import planning_prompt, writing_prompt
from app.utils import make_uuid, timestamp_now, ensure_sites_dir
import re
import random
from PIL import Image

# Налаштування logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"

SITES_DIR = ensure_sites_dir(os.getenv("SITES_DIR", "./sites"))

client = InferenceClient(model=MODEL, token=HF_TOKEN)
image_client = InferenceClient(model=IMAGE_MODEL, token=HF_TOKEN)

def inference(prompt: str, params: dict) -> dict:
    """Виклик Hugging Face API через сучасний клієнт."""
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
    """Виклик Hugging Face API для генерації зображення."""
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


env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

class SiteGenerator:
    def __init__(self):
        self.logs = []
        logger.info("SiteGenerator initialized")

    async def generate_sites(self, req):
        logger.info(f"Starting generation: {req.pages_count} pages about '{req.topic}' in {req.style} style")
        logger.info(f"Randomize temperature: {req.randomize_temperature}")
        
        results = []
        for i in range(req.pages_count):
            logger.info(f"Generating page {i+1}/{req.pages_count}")
            item = await self.generate_one_site(
                req.topic, 
                req.style, 
                req.temperature, 
                req.top_p, 
                req.max_tokens,
                req.generate_image,
                req.randomize_temperature,  # НОВИЙ ПАРАМЕТР
                req.temperature_min,         # НОВИЙ ПАРАМЕТР
                req.temperature_max          # НОВИЙ ПАРАМЕТР
            )
            results.append(item)
        
        self.logs.append({
            "topic": req.topic, 
            "count": req.pages_count, 
            "style": req.style,
            "time": timestamp_now()
        })
        logger.info(f"Generation completed: {len(results)} pages created")
        return results

    async def generate_one_site(self, topic: str, style: str, temperature: float, 
                                top_p: float, max_tokens: int, generate_image: bool = True,
                                randomize_temperature: bool = False,
                                temperature_min: float = 0.5,
                                temperature_max: float = 1.2):
        """Генерація одного сайту з покращеною варіативністю та контролем якості."""
        
        # 1) ВИЗНАЧЕННЯ ТЕМПЕРАТУРИ
        if randomize_temperature:
            # Повністю рандомна температура в заданому діапазоні
            actual_temp = random.uniform(temperature_min, temperature_max)
            logger.info(f"🎲 Random temperature generated: {actual_temp:.2f} (range: {temperature_min}-{temperature_max})")
        else:
            # Невелика варіація навколо заданого значення (±10%)
            variation = temperature * 0.1
            actual_temp = max(0.1, min(1.5, temperature + random.uniform(-variation, variation)))
            logger.info(f"📊 Temperature with slight variation: {actual_temp:.2f} (base: {temperature})")
        
        # 2) Планування структури
        plan_prompt_text = planning_prompt(topic, style)
        plan_resp = inference(plan_prompt_text, params={
            "temperature": actual_temp, 
            "top_p": top_p, 
            "max_new_tokens": 1000
        })
        
        plan_json = self._parse_plan_response(plan_resp, topic)
        plan_json["title"] = self._ensure_unique_title(plan_json.get("title", f"{topic} Guide"))

        # 3) ОПЦІЙНА ГЕНЕРАЦІЯ ЗОБРАЖЕННЯ
        site_id = make_uuid()
        image_path = None
        
        if generate_image:
            image_path = self._generate_and_save_image(plan_json, topic, site_id)

        # 4) Генерація контенту секцій
        # Можемо використати трохи іншу температуру для контенту
        content_temp = actual_temp
        if randomize_temperature:
            # Додаткова варіація для контенту (±0.05 від actual_temp)
            content_temp = max(0.1, min(1.5, actual_temp + random.uniform(-0.05, 0.05)))
            logger.info(f"📝 Content temperature: {content_temp:.2f}")
        
        generated_sections = self._generate_sections(
            topic, style, plan_json, content_temp, top_p, max_tokens
        )
        
        # 5) Вибір шаблону та рендеринг
        html = self._render_html(plan_json, generated_sections, image_path, style, topic)
        
        # 6) Збереження файлу
        file_path = os.path.join(SITES_DIR, f"site_{site_id}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        logger.info(f"Site saved: {file_path}")

        # 7) Запис у лог
        record = {
            "site_id": site_id,
            "title": plan_json.get("title"),
            "meta_description": plan_json.get("meta_description"),
            "image_path": image_path,
            "file_path": file_path,
            "style": style,
            "sections_count": len(generated_sections),
            "temperature_used": round(actual_temp, 2),  # НОВИЙ ПАРАМЕТР
            "created_at": timestamp_now()
        }
        self.logs.append(record)
        return record

    def _parse_plan_response(self, plan_resp: dict, topic: str) -> dict:
        """Парсинг JSON з fallback на дефолтну структуру."""
        try:
            raw_text = plan_resp if isinstance(plan_resp, str) else plan_resp.get("generated_text", "")
            
            # Спроба витягнути JSON з markdown блоку
            json_match = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = raw_text.strip()

            plan_json = json.loads(json_str)
            logger.info(f"Plan parsed successfully: {plan_json.get('title', 'No title')}")
            return plan_json
            
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}. Using fallback structure.")
            unique_suffix = make_uuid()[:8]
            return {
                "title": f"{topic} — Comprehensive Guide {unique_suffix}",
                "meta_description": f"Discover everything about {topic}. Expert insights and practical knowledge.",
                "image_prompt": f"Professional illustration representing {topic}",
                "sections": [
                    {"heading": "Introduction", "brief": f"Overview of {topic}"},
                    {"heading": "Key Features", "brief": f"Main aspects of {topic}"},
                    {"heading": "Summary", "brief": f"Conclusions about {topic}"}
                ]
            }

    def _ensure_unique_title(self, title: str) -> str:
        """Гарантує унікальність заголовка."""
        used_titles = {log.get("title") for log in self.logs if log.get("title")}
        original_title = title
        suffix_count = 1
        
        while title in used_titles:
            title = f"{original_title} ({make_uuid()[:6]})"
            suffix_count += 1
            if suffix_count > 10:
                break
        
        if title != original_title:
            logger.info(f"Title made unique: {title}")
        return title

    def _generate_and_save_image(self, plan_json: dict, topic: str, site_id: str) -> Optional[str]:
        """Генерує та зберігає зображення."""
        image_prompt = plan_json.get("image_prompt", f"Professional illustration of {topic}")
        image = inference_image(image_prompt)
        
        if image:
            image_path = f"image_{site_id}.png"
            abs_image_path = os.path.join(SITES_DIR, image_path)
            image.save(abs_image_path)
            logger.info(f"Image saved: {abs_image_path}")
            return image_path
        else:
            logger.warning("Image generation failed")
            return None

    def _generate_sections(self, topic: str, style: str, plan_json: dict,
                          temperature: float, top_p: float, max_tokens: int) -> list:
        """Генерує контент для всіх секцій з урахуванням стилю."""
        from app.prompts import STYLE_INSTRUCTIONS
        
        sections_data = plan_json.get("sections", [])
        write_prompt = writing_prompt(topic, style, plan_json.get("title", ""), sections_data)
        
        logger.info(f"Generating content for {len(sections_data)} sections")
        
        write_resp = inference(write_prompt, params={
            "temperature": temperature, 
            "top_p": top_p, 
            "max_new_tokens": max_tokens
        })
        
        full_text = write_resp if isinstance(write_resp, str) else write_resp.get("generated_text", "")
        
        return self._extract_sections(full_text, sections_data)

    def _extract_sections(self, full_text: str, sections_data: list) -> list:
        """Витягує секції з згенерованого тексту."""
        parts = full_text.split("###")
        generated_sections = []
        
        for s in sections_data:
            heading = s.get("heading", "")
            content = ""
            
            # Шукаємо відповідну секцію в згенерованому тексті
            for part in parts[1:]:
                part_stripped = part.strip()
                if part_stripped.startswith(heading + "\n"):
                    content = part_stripped[len(heading) + 1:].strip()
                    break
                elif part_stripped.startswith(heading):
                    rest = part_stripped[len(heading):].lstrip()
                    content = rest
                    break
            
            # Fallback на brief якщо контент не знайдено
            if not content:
                content = s.get("brief", f"Information about {heading}")
                logger.warning(f"No content found for section '{heading}', using brief")
            
            # Очищення зайвих пробілів
            content = ' '.join(content.split())
            generated_sections.append({"heading": heading, "content": content})
        
        logger.info(f"Extracted {len(generated_sections)} sections")
        return generated_sections

    def _render_html(self, plan_json: dict, sections: list, image_path: Optional[str],
                    style: str, topic: str) -> str:
        """Рендерить HTML з відповідним шаблоном."""
        template_map = {
            "educational": "educational.html",
            "marketing": "marketing.html",
            "technical": "technical.html",
            "minimalist": "minimalist.html",
            "creative": "creative.html",
            "casual": "base.html",
        }
        template_name = template_map.get(style.lower(), "educational.html")
        image_url = f"/image/{image_path}" if image_path else None
        tpl = env.get_template(template_name)
        html = tpl.render(
            title=plan_json.get("title", "Untitled"),
            meta_description=plan_json.get("meta_description", f"Learn about {topic}"),
            sections=sections,
            image_path=image_url,
            generated_at=datetime.utcnow().isoformat() + "Z"
        )
        
        logger.info(f"HTML rendered using template: {template_name}")
        return html

    def get_site_path(self, site_id: str) -> Optional[str]:
        """Отримує шлях до файлу сайту за ID."""
        for r in self.logs:
            if r.get("site_id") == site_id:
                return r.get("file_path")
        logger.warning(f"Site not found: {site_id}")
        return None

    def get_logs(self) -> list:
        """Повертає всі логи генерації."""
        return self.logs