from enum import StrEnum

import os
import re
from typing import Any, Dict

class FileType(StrEnum):
    PDF = 'pdf'
    DOC = 'doc'
    VISUAL = 'visual'
    AURAL = 'aural'
    VIRTUAL = 'virtual'
    FOLDER = 'folder'
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

    
def parse_file_info(file: Any) -> Dict[str, Any]:
    file_info = {
        "file_name": file.name,
        "file_size": file.size,
        "file_type": filename_type(file.name),
        "file_source": FileSource.LOCAL
    }
    return file_info

def filename_type(filename):
    filename = filename.lower()
    if re.match(r".*\.pdf$", filename):
        return FileType.PDF.value

    if re.match(
             r".*\.(eml|doc|docx|ppt|pptx|yml|xml|htm|json|csv|txt|ini|xls|xlsx|wps|rtf|hlp|pages|numbers|key|md|py|js|java|c|cpp|h|php|go|ts|sh|cs|kt|html|sql)$", filename):
        return FileType.DOC.value

    if re.match(
            r".*\.(wav|flac|ape|alac|wavpack|wv|mp3|aac|ogg|vorbis|opus|mp3)$", filename):
        return FileType.AURAL.value

    if re.match(r".*\.(jpg|jpeg|png|tif|gif|pcx|tga|exif|fpx|svg|psd|cdr|pcd|dxf|ufo|eps|ai|raw|WMF|webp|avif|apng|icon|ico|mpg|mpeg|avi|rm|rmvb|mov|wmv|asf|dat|asx|wvx|mpe|mpa|mp4)$", filename):
        return FileType.VISUAL.value

    return FileType.OTHER.value