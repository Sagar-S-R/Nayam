import bleach
import magic
import re
from typing import Optional

def sanitize_text(text: Optional[str]) -> Optional[str]:
    """
    Strips all HTML tags and script content from a text string.
    Returns the sanitized string, or None if the input is None.
    """
    if text is None:
        return None
        
    # 1. Completely remove `<script>...</script>` tags and their inner payload
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 2. Strip all remaining HTML tags
    sanitized = bleach.clean(text, tags=[], attributes={}, strip=True)
    return sanitized.strip()

def validate_mime_type(file_bytes: bytes, allowed_mimes: list[str] = None) -> str:
    """
    Validates a file's true MIME type using its magic number bytes.
    Raises ValueError if the MIME type is not in the allowed list.
    """
    if allowed_mimes is None:
        allowed_mimes = [
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
            "application/msword" # doc
        ]
        
    mime_type = magic.from_buffer(file_bytes, mime=True)
    if mime_type not in allowed_mimes:
        raise ValueError(f"Invalid file type: {mime_type}.")
        
    return mime_type
