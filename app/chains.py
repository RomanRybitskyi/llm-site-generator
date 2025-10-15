# app/chains.py
import os
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace # <--- 1. Імпортуємо ChatHuggingFace
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

# 2. Створюємо базовий endpoint, як і раніше
endpoint = HuggingFaceEndpoint(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    max_tokens=2048 # Можна встановити загальний ліміт тут
)

# 3. Обгортаємо endpoint у ChatHuggingFace.
# Тепер змінна `llm` є повноцінною чат-моделлю для LangChain.
# Решта коду працюватиме без змін!
llm = ChatHuggingFace(llm=endpoint)

# Функція для отримання КОМПОНЕНТІВ ланцюжка планування (без змін)
def get_planning_components():
    """Повертає шаблон промпту та парсер для ланцюжка планування."""
    prompt_text = """
You are an expert web content planner creating a structure for a website about: "{topic}".
Style: {style}

Create a JSON structure with these fields:
- title: A compelling, clear title (max 70 characters)
- meta_description: An engaging description (50-160 chars)
- image_prompt: A detailed, vivid description for generating an image (20-50 words)
- sections: An array of objects based on these headings: {sections_str}
Each section object must have:
  - "heading": The exact heading from the list
  - "brief": A clear, specific 1-sentence description of what this section should cover

CRITICAL RULES:
1. Return ONLY valid JSON. No markdown, no explanations.
2. Use double quotes for all JSON strings.
Return the JSON now:
    """
    prompt_template = PromptTemplate.from_template(prompt_text)
    json_parser = JsonOutputParser()
    
    return prompt_template, json_parser

# Функція для отримання КОМПОНЕНТІВ ланцюжка написання (без змін)
def get_writing_components():
    """Повертає шаблон промпту та парсер для ланцюжка написання."""
    prompt_text = """
You are writing content for a website titled "{title}" about {topic}.
STYLE: {style} - {style_instr}
APPROACH: {style_guide}

Write content for the following sections. Each section must be {word_count} words.

CRITICAL FORMATTING RULES:
- Start each section with: ### [Section Heading]
- Write the paragraph immediately after the heading
- Do NOT repeat the heading in the content

{sections_to_write}

Remember:
- Write in {style} style throughout
- Stay focused on {topic}
Begin writing now:
    """
    prompt_template = PromptTemplate.from_template(prompt_text)
    string_parser = StrOutputParser()
    
    return prompt_template, string_parser