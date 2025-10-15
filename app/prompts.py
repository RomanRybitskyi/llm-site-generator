# app/prompts.py
import random

# ... (INTRO_SECTIONS, CORE_SECTIONS, OUTRO_SECTIONS, STYLE_INSTRUCTIONS залишаються без змін) ...
INTRO_SECTIONS = ["Introduction", "Overview"]
CORE_SECTIONS = [
    "Use Cases", "Technical Details", "Key Features",
    "Tools and Libraries", "Examples", "Comparison",
    "Best Practices", "Common Challenges", "FAQ"
]
OUTRO_SECTIONS = ["Summary", "Conclusion", "Summary and CTA"]
STYLE_INSTRUCTIONS = {
    "educational": "Explain clearly and step-by-step, suitable for learners.",
    "marketing": "Catchy, benefit-focused, persuasive tone, short paragraphs.",
    "technical": "Detailed, include code examples or pseudo-code if relevant.",
    "minimalist": "Concise, clean, focus on essential information only.",
    "creative": "Engaging, imaginative, use storytelling elements.",
    "casual": "Friendly, conversational tone, easy to read.",
}


def choose_sections(min_n=3, max_n=5):
    # ... (Ця функція залишається без змін) ...
    intro = random.choice(INTRO_SECTIONS)
    core_count = random.randint(max(1, min_n - 2), max(1, max_n - 2))
    core = random.sample(CORE_SECTIONS, min(core_count, len(CORE_SECTIONS)))
    outro = random.choice(OUTRO_SECTIONS)
    return [intro] + core + [outro]

# planning_prompt більше не потрібен, оскільки його логіка тепер у app/chains.py

# writing_prompt ми будемо використовувати для підготовки вхідних даних для ланцюжка
def prepare_writing_inputs(topic: str, style: str, title: str, sections: list) -> dict:
    """
    Готує словник з даними для ланцюжка написання контенту.
    """
    style_instr = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["educational"])
    style_specific = {
        "educational": "Use clear explanations, define terms, provide examples.",
        "marketing": "Use persuasive language, emphasize benefits, include strong calls-to-action.",
        "technical": "Include technical details, code examples if relevant, precise terminology.",
        "minimalist": "Be concise and direct. Every word must count.",
        "creative": "Use vivid language, metaphors, storytelling.",
        "casual": "Write conversationally, use simple language."
    }
    word_counts = {
        "educational": "80-120", "marketing": "60-90", "technical": "100-150",
        "minimalist": "40-70", "creative": "90-130", "casual": "70-100"
    }

    # Форматуємо секції для передачі в промпт
    sections_to_write = ""
    for i, s in enumerate(sections, 1):
        sections_to_write += f"""
Section {i}: ### {s.get("heading", "Section")}
Purpose: {s.get("brief", "")}
---
"""
    
    return {
        "topic": topic,
        "style": style,
        "title": title,
        "style_instr": style_instr,
        "style_guide": style_specific.get(style, style_specific["educational"]),
        "word_count": word_counts.get(style, "80-120"),
        "sections_to_write": sections_to_write.strip()
    }