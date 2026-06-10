import re
from pathlib import Path
from typing import Optional

from tools.registry import tool
from core.extractor import PDFExtractor

_extractor = PDFExtractor()


@tool(
    name="search_pdf",
    description="Search for a keyword or regex pattern in a PDF's extracted text.",
    file_path={"type": "string", "description": "Path to the PDF file"},
    pattern={"type": "string", "description": "Keyword or regex pattern to search for"},
    case_sensitive={"type": "boolean", "description": "Whether search is case-sensitive", "default": False},
)
def search_pdf(file_path: str, pattern: str, case_sensitive: bool = False) -> dict:
    extraction = _extractor.extract(Path(file_path))
    flags = 0 if case_sensitive else re.IGNORECASE
    matches = []
    for i, line in enumerate(extraction.content.splitlines(), 1):
        if re.search(pattern, line, flags):
            matches.append({"line": i, "text": line.strip()})
    return {
        "filename": extraction.filename,
        "pattern": pattern,
        "match_count": len(matches),
        "matches": matches[:100],
    }


@tool(
    name="search_batch",
    description="Search multiple PDFs for a pattern.",
    file_paths={"type": "array", "items": {"type": "string"}, "description": "List of PDF paths"},
    pattern={"type": "string", "description": "Pattern to search for"},
    case_sensitive={"type": "boolean", "description": "Case-sensitive flag", "default": False},
)
def search_batch(file_paths: list[str], pattern: str, case_sensitive: bool = False) -> list[dict]:
    return [
        search_pdf(fp, pattern, case_sensitive=case_sensitive) for fp in file_paths
    ]
