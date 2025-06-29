from enum import StrEnum

import os
from typing import Any, Dict

class FileType(StrEnum):
    FOLDER = "folder"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    PPT = "ppt"
    VISUAL = "visual"
    TEXT = "txt"
    HTML = "html"
    OTHER = "other"

class FileSource(StrEnum):
    LOCAL = "local"
    KNOWLEDGE_BASE = "knowledge_base"
    S3 = "s3"
    
class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INIT = "init"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def filename_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.docx':
        return 'docx'
    elif ext == '.doc':
        return 'doc'
    elif ext == '.txt':
        return 'txt'
    
def parse_file_info(file: Any) -> Dict[str, Any]:
    file_info = {
        "file_name": file.name,
        "file_size": file.size,
        "file_type": filename_type(file.name),
        "file_source": FileSource.LOCAL
    }
    return file_info

