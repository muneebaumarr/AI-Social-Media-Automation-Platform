import google.generativeai as genai
import json
import re



from app.config import GEMINI_API_KEY


genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "temperature":       0.9,
        "top_p":             0.95,
        "max_output_tokens": 8192,
    },
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

def repurpose_for_platform(
    draft_title:   str,
    draft_content: str,
    platform:      str,
    brand_context: dict = None,
) -> dict:
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
        f"HASHTAGS: Generate exactly {rule['hashtag_count']} — put them ONLY in the hashtags field, never in the post body.\n"
    )

    # Build the brand context section
    brand_section = ""
    if brand_context:
        parts = []
        if brand_context.get("brand_name"):
            parts.append(f"BRAND NAME: {brand_context['brand_name']}")
        if brand_context.get("industry"):
            parts.append(f"INDUSTRY: {brand_context['industry']}")
        if brand_context.get("brand_voice"):
            parts.append(f"BRAND VOICE & TONE: {brand_context['brand_voice']}")
        if brand_context.get("target_audience"):
            parts.append(f"TARGET AUDIENCE: {brand_context['target_audience']}")
        if brand_context.get("do_not_use"):
            parts.append(f"AVOID THESE: {brand_context['do_not_use']}")
        if brand_context.get("social_handle"):
            parts.append(f"{platform.upper()} HANDLE: {brand_context['social_handle']}")

        if parts:
            brand_section = "BRAND CONTEXT:\n" + "\n".join(parts) + "\n\n"

    prompt = f"""You are a social media expert writing content for a specific brand.

{brand_section}ORIGINAL TITLE: {draft_title}
ORIGINAL CONTENT: {draft_content}

PLATFORM INSTRUCTIONS: {platform_block}

{HUMANIZE_RULES}

CRITICAL RULES:
1. Match the BRAND VOICE exactly — this is more important than anything else
2. Write FOR the target audience, not at them
3. Strictly avoid anything in "AVOID THESE"
4. Output ONLY a JSON object, nothing else
5. Do NOT use markdown code blocks
6. Inside JSON strings, escape any double quotes with \\"
7. The "repurposed_content" must be COMPLETE — do not cut it short
8. Start your response with {{ and end with }}

Required JSON format:
{{
  "repurposed_content": "the COMPLETE post text",
  "caption": "the hook or short caption",
  "hashtags": "space-separated hashtags starting with #"
}}"""

    response = None
    try:
        response = model.generate_content(prompt)
        raw = response.text or ""

        # Strip markdown fences Gemini sometimes adds
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        # Extract the first {...} block in case there's leading/trailing text
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        data = json.loads(cleaned)

        return {
            "platform":           platform,
            "repurposed_content": data.get("repurposed_content", "").strip(),
            "caption":            data.get("caption", "").strip(),
            "hashtags":           data.get("hashtags", "").strip(),
            "prompt":             prompt,
            "success":            True,
        }

    except Exception as e:
        raw_preview = (response.text[:300] if response and response.text else "no response")
        print(f"AI error for {platform}: {e}")
        print(f"Raw response: {raw_preview}")
        return {
            "platform":           platform,
            "repurposed_content": "",
            "caption":            "",
            "hashtags":           "",
            "error":              str(e),
            "success":            False,
        }


def repurpose_for_platforms(
    draft_title:    str,
    draft_content:  str,
    platforms:      list,
    brand_context:  dict = None,
    social_handles: dict = None,
) -> list:
    """
    Generates content for multiple platforms with brand context.

    social_handles is a dict like {'instagram': '@acmecoffee', 'linkedin': ...}
    """
    results = []
    for platform in platforms:
        ctx = dict(brand_context) if brand_context else {}
        if social_handles and platform in social_handles:
            ctx["social_handle"] = social_handles[platform]

        result = repurpose_for_platform(
            draft_title   = draft_title,
            draft_content = draft_content,
            platform      = platform,
            brand_context = ctx if ctx else None,
        )
        results.append(result)
    return results


def generate_weekly_recommendation(platform_stats: list[dict],
                                   total_posts: int) -> dict:
    """
    Asks Gemini to recommend what to post next week based on analytics.
    Returns {best_platform, recommendation_text}.
    """
    if not platform_stats or total_posts == 0:
        return {
            "best_platform":       "instagram",
            "recommendation_text": "Start by creating your first few posts. "
                                   "Once you have engagement data, we'll "
                                   "give you personalized recommendations.",
        }

    # Build a data summary for Gemini
    summary_lines = []
    for p in platform_stats:
        summary_lines.append(
            f"- {p['platform'].title()}: {p['post_count']} posts, "
            f"{p['avg_rate']}% avg engagement, "
            f"{p['likes']} likes, {p['comments']} comments"
        )
    summary = "\n".join(summary_lines)

    # Find best platform from the data
    best_platform = max(platform_stats, key=lambda x: x["avg_rate"])["platform"]

    prompt = f"""You are a social media strategist analyzing weekly analytics.

WEEKLY DATA:
{summary}

Based on this data, write 2-3 specific actionable recommendations for next week. Be concrete:
- Which platform to focus on
- What type of content performs best there
- Optimal posting frequency

Keep it under 80 words. Direct, data-driven tone. No fluff."""

    try:
        response   = model.generate_content(prompt)
        rec_text   = response.text.strip()
    except Exception as e:
        print(f"[AI ERROR] Weekly recommendation: {e}")
        rec_text = (f"Focus on {best_platform.title()} next week — "
                    f"it's your highest-engagement platform. "
                    f"Aim for 3-4 quality posts.")

    return {
        "best_platform":       best_platform,
        "recommendation_text": rec_text,
    }