import json
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.config import get_settings

logger = logging.getLogger(__name__)

def extract_meeting_minutes(transcript: str, db: Session) -> Dict[str, Any]:
    settings = get_settings()
    
    SYSTEM_PROMPT = '''You are an expert Government Meeting AI. Read the provided raw transcript of a municipal meeting.
Extract and output ONLY a valid JSON object matching this schema exactly:
{
  "summary": "overall summary of the meeting",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [
    {
      "task": "description of the action",
      "department": "responsible department or 'Unassigned'",
      "deadline": "suggested deadline from context, or 'As soon as possible'"
    }
  ],
  "departments": ["dept 1", "dept 2"],
  "priority_issues": ["issue 1", "issue 2"]
}
Do not include markdown blocks, just raw JSON.'''

    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY must be set for Meeting Mode LLM extraction.")

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Transcript:\n\n{transcript[:8000]}"},
            ],
            temperature=0.1, # low temp for structured output
        )
        content = response.choices[0].message.content
        # parse json
        try:
            # handle markdown block
            if "`json" in content:
                content = content.split("`json")[1].split("`")[0].strip()
            data = json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse meeting json: {e}")
            data = {"summary": "Failed to extract summary.", "key_decisions": [], "action_items": [], "departments": [], "priority_issues": []}
            
        return data
    except Exception as e:
        logger.error(f"Meeting extraction LLM call failed: {e}")
        raise e
