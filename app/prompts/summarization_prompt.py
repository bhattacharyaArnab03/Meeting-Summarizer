SUMMARY_PROMPT = """You are an expert meeting analyst. Convert the transcript below into a concise, actionable meeting record.

Return only valid JSON matching this exact shape:
{{
  "executive_summary": "string",
  "key_points": ["string"],
  "decisions": ["string"],
  "action_items": [{{"task": "string", "owner": "string or null", "deadline": "string or null"}}],
  "risks": ["string"],
  "follow_ups": ["string"]
}}

Rules:
- Use only information contained in the transcript. Never invent people, owners, deadlines, decisions, risks, or commitments.
- Distinguish finalized decisions from discussion, options, and proposals. Put only finalized decisions in decisions.
- Include an action item only when the transcript supports an actual task or agreed next step.
- Set owner only when explicitly stated or unambiguous in the transcript; otherwise use null.
- Set deadline only when explicitly stated or clearly given; otherwise use null.
- Use empty arrays when the transcript does not support an item.
- Preserve important domain terminology and ignore conversational filler.
- Prefer concise, actionable wording.

TRANSCRIPT:
---
{transcript}
---
"""


def build_summary_prompt(transcript: str) -> str:
    return SUMMARY_PROMPT.format(transcript=transcript)


TRANSCRIPTION_PROMPT = """Transcribe this meeting recording completely and accurately. Return only the transcript text.
Do not summarize, omit, or invent content. Preserve speaker changes with labels such as Speaker 1 when identifiable.
Include all substantive words, decisions, tasks, names, dates, and risks. Ignore only non-speech noise.
"""
