import google.generativeai as genai
import json 
import re
import os


from app.config import GEMINI_API_KEY


genai.configure(api_key=GEMINI_API_KEY)
# Configuration for more creative output
generation_config = {
    "temperature":      0.9,    # Higher = more creative (0.0 to 1.0)
    "top_p":            0.95,   # Nucleus sampling
    "max_output_tokens": 1024,  # Maximum response length
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
)

# Rules for each platform

PLATEFORM_RULES = {
    "instagram": {
        "tone": (
            "Warm, personal, and real — like a friend sharing something that genuinely moved them. "
            "Write in first person. Speak directly to the reader. Be specific, not vague."
        ),
        "format": (
            "Start with a one-line hook that stops the scroll — a surprising fact, a short question, or a bold statement. "
            "Write 150-200 words. Use short sentences. Break lines for readability. "
            "Use 2-3 emojis placed naturally, not at every line. End with a clear call to action or a question. "
            "Do NOT include any hashtags inside the post body — they go in the hashtags field only."
        ),
        "storytelling": (
            "Open with a specific moment or observation. Build a small tension. Land on a useful insight or feeling. "
            "Do NOT describe or reference any image, photo, or visual. Write purely as text copy."
        ),
        "hashtag_count": "8-10 relevant hashtags",
    },
    "linkedin": {
        "tone": (
            "Confident but humble — like a mentor sharing a real lesson they learned the hard way. "
            "Write like a person, not a brand. Be direct and honest. Show a point of view."
        ),
        "format": (
            "Start with a single bold line that earns the click to 'see more'. "
            "Use short paragraphs — 1 to 2 sentences each. Write 200-300 words. "
            "End with a genuine question that invites real replies. "
            "Do NOT include any hashtags inside the post body — they go in the hashtags field only."
        ),
        "storytelling": (
            "Open with a specific moment, number, or turning point — not a broad claim. "
            "Move from problem to lesson to takeaway. Make the reader feel the insight, not just read it."
        ),
        "hashtag_count": "3-5 professional hashtags",
    },
    "twitter": {
        "tone": (
            "Sharp, direct, and a little opinionated — like a smart friend sending you a text they couldn't keep to themselves. "
            "Write one clear idea. No throat-clearing. No buildup."
        ),
        "format": (
            "Keep the post body under 240 characters — leave room for hashtags. "
            "Make it punchy and quotable. Use plain language. "
            "End with a short question or a line that makes people want to reply. "
            "Do NOT include any hashtags inside the post body — they go in the hashtags field only."
        ),
        "storytelling": (
            "One idea. One punch. The best tweets sound like something you wish you'd said first."
        ),
        "hashtag_count": "2-3 tight, relevant hashtags",
    },
    "facebook": {
        "tone": (
            "Warm and conversational — like telling a story at the dinner table to people you actually like. "
            "Relatable, grounded, and a little bit personal. Write like a real human, not a marketer."
        ),
        "format": (
            "Write 100-150 words. Use simple, short sentences. "
            "Open with a line that makes someone stop scrolling. End with a question that feels natural, not forced. "
            "Do NOT include any hashtags inside the post body — they go in the hashtags field only."
        ),
        "storytelling": (
            "Share something specific and real. A moment, a realization, a small story with a payoff. "
            "Avoid generic observations. Make the reader nod and say 'same'."
        ),
        "hashtag_count": "3-4 broad hashtags",
    },
}

# Core writing rules injected into every prompt
HUMANIZE_RULES = (
    "WRITING RULES — follow these strictly:\n"
    "- Write like a real person. Use simple, everyday English. Short sentences win.\n"
    "- Be a storyteller first, copywriter second. Every good post has a hook, a tension, and a payoff.\n"
    "- NEVER use these overused AI words or phrases: game-changer, leverage, synergy, unlock, dive deep, "
    "  it's no secret, the reality is, cutting-edge, innovative, transform, revolutionize, in today's fast-paced world, "
    "  groundbreaking, seamlessly, robust, testament, pivotal, navigate, landscape, delve, empower, "
    "  foster, elevate, crucial, utilize, facilitate, in conclusion, at the end of the day.\n"
    "- Avoid stacking adjectives. One strong word beats three weak ones.\n"
    "- Do NOT reference, describe, or suggest any image, stock photo, or visual element.\n"
    "- Do NOT write captions that sound like they belong under a generic stock photo.\n"
    "- Write in active voice. Passive voice makes copy feel slow and corporate.\n"
    "- Be specific. 'I lost 3 clients in one week' beats 'I faced some challenges'.\n"
    "- Sound like a smart human, not an AI trying to sound human.\n"
)

def repurpose_for_platform(draft_title: str, draft_content: str, platform: str) -> dict:
    """
    Calls Gemini to repurpose draft content for a specific platform.
    Returns a dictionary with repurposed_content, caption, and hashtags.
    """
    rule = PLATEFORM_RULES.get(platform, PLATEFORM_RULES["instagram"])

    platform_block = (
        f"PLATFORM: {platform.upper()}\n"
        f"TONE: {rule['tone']}\n"
        f"FORMAT: {rule['format']}\n"
        f"STORYTELLING: {rule['storytelling']}\n"
        f"HASHTAGS: Generate exactly {rule['hashtag_count']} — put them ONLY in the hashtags JSON field, never in the post body.\n"
    )

    prompt = f"""You are a human copywriter and storyteller with 10 years of experience writing viral social media content. \
You write with personality, clarity, and purpose. You never sound like AI. You never use buzzwords. \
You write copy that makes real people stop, read, and feel something.

Your job: repurpose the content below into a native {platform} post.

---
ORIGINAL TITLE: {draft_title}
ORIGINAL CONTENT: {draft_content}
---

{HUMANIZE_RULES}

{platform_block}
OUTPUT RULES:
- "repurposed_content": the full post body — NO hashtags inside it, ever.
- "caption": the single hook line only — the very first sentence that stops the scroll.
- "hashtags": space-separated hashtags starting with # — ALL hashtags go here, nowhere else.

Respond ONLY with valid JSON. No markdown, no code blocks, no explanation — just raw JSON:
{{
  "repurposed_content": "...",
  "caption": "...",
  "hashtags": "..."
}}"""

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # ─── Clean the response thoroughly ──────────────────────
        # Remove markdown code blocks
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text)
        cleaned = re.sub(r"\s*```", "", cleaned)
        cleaned = cleaned.strip()

        # Extract just the JSON object using regex
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)

        # Parse JSON
        data = json.loads(cleaned)

        return {
            "platform":           platform,
            "repurposed_content": data.get("repurposed_content", "").strip(),
            "caption":            data.get("caption", "").strip(),
            "hashtags":           data.get("hashtags", "").strip(),
            "prompt":             prompt,
            "success":            True,
        }

    except json.JSONDecodeError as e:
        # Fallback if Gemini returns invalid JSON
        print(f"JSON parse error for {platform}: {e}")
        print(f"Raw response: {raw_text[:200]}")
        return {
            "platform":           platform,
            "repurposed_content": raw_text,
            "caption":            "",
            "hashtags":           "",
            "prompt":             prompt,
            "success":            True,
        }

    except Exception as e:
        print(f"AI error for {platform}: {e}")
        return {
            "platform":           platform,
            "repurposed_content": "",
            "caption":            "",
            "hashtags":           "",
            "error":              str(e),
            "success":            False,
        }
