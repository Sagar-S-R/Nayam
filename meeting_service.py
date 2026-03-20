import json
import logging
import os
import uuid
from typing import Dict, Any

from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.stt import STTService, transcribe_audio, _save_audio, _cleanup_file
from app.models.draft import Draft
from app.models.action import ActionRequest

logger = logging.getLogger(__name__)

async def process_meeting_audio(file: UploadFile, db: Session, user_id: str) -> Dict[str, Any]:
    from meeting_mode import extract_meeting_minutes
    # 1. Save and Transcribe
    audio_path, raw_bytes = await _save_audio(file)
    try:
        transcript, language, duration, provider = transcribe_audio(audio_path)
        
        if not transcript:
            raise ValueError("Meeting transcription returned empty.")
            
        # 2. LLM Extraction
        extraction = extract_meeting_minutes(transcript, db)
        
        # 3. Create Draft (MoM)
        meeting_title = "Minutes of Meeting - " + datetime.now().strftime("%Y-%m-%d")
        draft_content = f"# {meeting_title}\n\n"
        draft_content += f"## Summary\n{extraction.get('summary', '')}\n\n"
        
        draft_content += "## Key Decisions\n"
        for d in extraction.get("key_decisions", []):
            draft_content += f"- {d}\n"
            
        draft_content += "\n## Action Items\n"
        for a in extraction.get("action_items", []):
            draft_content += f"- **{a.get('task')}** (Dept: {a.get('department')}, Due: {a.get('deadline')})\n"
            
        draft = Draft(
            id=uuid.uuid4(),
            author_id=user_id,
            title=meeting_title,
            content=draft_content,
            draft_type="meeting_agenda",
        )
        db.add(draft)
        
        # 4. Create Action Requests
        created_actions = 0
        for action in extraction.get("action_items", []):
            req = ActionRequest(
                id=uuid.uuid4(),
                title=action.get("task", "Meeting Action Item")[:200],
                description=f"Assigned to: {action.get('department', 'Unassigned')}\\nDeadline: {action.get('deadline', 'TBD')}",
                status="pending",
                category="meeting_task",
                priority="high",
            )
            db.add(req)
            created_actions += 1
            
        db.commit()
        
        return {
            "transcript": transcript,
            "provider": provider,
            "extraction": extraction,
            "meeting_draft_id": str(draft.id),
            "created_action_requests": created_actions
        }
            
    finally:
        _cleanup_file(audio_path)
