# app/prompts.py
import random

# Always at the beginning
INTRO_SECTIONS = ["Introduction", "Overview"]

# Core content sections (can be in any order)
CORE_SECTIONS = [
    "Use Cases", "Technical Details", "Key Features",
    "Tools and Libraries", "Examples", "Comparison",
    "Best Practices", "Common Challenges", "FAQ"
]

# Always at the end
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
    """
    Select sections in logical order:
    1. Start with Introduction or Overview
    2. Add 1-3 core sections from CORE_SECTIONS
    3. End with Summary/Conclusion
    """
    intro = random.choice(INTRO_SECTIONS)
    core_count = random.randint(max(1, min_n - 2), max(1, max_n - 2))
    core = random.sample(CORE_SECTIONS, min(core_count, len(CORE_SECTIONS)))
    outro = random.choice(OUTRO_SECTIONS)
    
    return [intro] + core + [outro]

def planning_prompt(topic: str, style: str, existing_titles: list = None):
    sections = choose_sections()
    style_instr = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["educational"])

    uniqueness_instruction = ""
    if existing_titles:
        titles_str = '", "'.join(existing_titles)
        uniqueness_instruction = f'''
CRITICAL ADDITIONAL RULE:
You MUST generate a completely new title that is semantically different from these already used titles: "{titles_str}".
Focus on a different angle, benefit, or keyword.
'''
    
    prompt = f"""
You are an expert web content planner creating a structure for a website about: "{topic}".
Style: {style} - {style_instr}
{uniqueness_instruction}

Create a JSON structure with these fields:
- title: A compelling, clear title (max 70 characters) that captures the essence of {topic}
- meta_description: An engaging description (50-160 chars) that would make someone want to click
- image_prompt: A detailed, vivid description for generating an image (20-50 chars). Be specific and visual.
- sections: An array of EXACTLY {len(sections)} section objects

For sections array, use these headings in EXACT order: {', '.join(sections)}
Each section object must have:
  - "heading": The exact heading from the list above
  - "brief": A clear, specific 1-sentence description of what this section should cover

CRITICAL RULES:
1. First section ({sections[0]}) must introduce the topic clearly
2. Middle sections provide detailed information, examples, or insights
3. Last section ({sections[-1]}) must conclude or provide a call-to-action
4. Return ONLY valid JSON - no markdown code blocks, no explanations, no extra text
5. Use double quotes for all JSON strings
6. Each "brief" should be specific to the topic, not generic

Example of good briefs:
- "Explain what {topic} is and why it matters"
- "List 3-5 practical applications of {topic} in real-world scenarios"
- "Summarize key takeaways and encourage readers to explore {topic} further"

Return the JSON now:"""
    return prompt


def writing_prompt(topic: str, style: str, title: str, sections: list) -> str:
    """Generate content prompt with style consideration."""
    style_instr = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["educational"])
    
    style_specific = {
        "educational": "Use clear explanations, define terms, provide examples. Write in an informative, structured way.",
        "marketing": "Use persuasive language, emphasize benefits, include strong calls-to-action. Be energetic and engaging.",
        "technical": "Include technical details, code examples if relevant, precise terminology. Be thorough and accurate.",
        "minimalist": "Be concise and direct. Every word must count. Focus on essential information only.",
        "creative": "Use vivid language, metaphors, storytelling. Make it memorable and engaging.",
        "casual": "Write conversationally, use simple language. Be friendly and approachable."
    }
    
    style_guide = style_specific.get(style, style_specific["educational"])
    
    word_counts = {
        "educational": "80-120",
        "marketing": "60-90",
        "technical": "100-150",
        "minimalist": "40-70",
        "creative": "90-130",
        "casual": "70-100"
    }
    word_count = word_counts.get(style, "80-120")
    
    prompt = f"""You are writing content for a website titled "{title}" about {topic}.

STYLE: {style} - {style_instr}
APPROACH: {style_guide}

Write content for the following sections. Each section must be {word_count} words.

CRITICAL FORMATTING RULES:
- Start each section with: ### [Section Heading]
- Write the paragraph immediately after the heading
- Do NOT repeat the heading in the content
- Use the ### separator ONLY between sections
- Each paragraph should flow naturally and be engaging

"""
    
    for i, s in enumerate(sections, 1):
        heading = s.get("heading", "Section")
        brief = s.get("brief", "")
        prompt += f"""
Section {i}: ### {heading}
Purpose: {brief}
Write {word_count} words that fit the {style} style. Be specific to {topic}.

"""
    
    prompt += f"""
Remember:
- Write in {style} style throughout
- Each section: {word_count} words
- Use ### before each heading
- Make content unique and engaging
- Stay focused on {topic}

Begin writing now:"""
    
    return prompt