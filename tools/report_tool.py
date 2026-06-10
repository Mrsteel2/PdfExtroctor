from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from tools.registry import tool
from core.extractor import PDFExtractor
from core.summarizer import Summarizer
from config import get_settings

logger = logging.getLogger(__name__)

_extractor = PDFExtractor()


def _get_summarizer():
    settings = get_settings()
    if settings.openrouter_api_key:
        return Summarizer()
    return None


@tool(
    name="generate_report",
    description="Generate a consolidated report from one or more PDFs.",
    file_paths={"type": "array", "items": {"type": "string"}, "description": "List of PDF paths"},
    output_path={"type": "string", "description": "Output path for report file (optional)"},
)
def generate_report(file_paths: list[str], output_path: Optional[str] = None) -> dict:
    extractions = _extractor.extract_batch([Path(p) for p in file_paths])

    summarizer = _get_summarizer()
    if summarizer:
        summaries = summarizer.summarize_batch(extractions)
    else:
        logger.info("No OpenRouter API key set; using raw content in report")
        summaries = None

    lines = [
        f"# PDF Extraction Report",
        f"Generated: {datetime.now().isoformat()}",
        f"Source files: {len(file_paths)}",
        "",
    ]

    if summaries:
        for s in summaries:
            lines.extend([
                f"## {s.extraction.filename}",
                f"Pages: {s.extraction.page_count or 'N/A'}",
                f"Model: {s.model} | Tokens: {s.tokens_used}",
                "",
                s.summary,
                "",
                "---",
                "",
            ])
    else:
        for ext in extractions:
            lines.extend([
                f"## {ext.filename}",
                f"Pages: {ext.page_count or 'N/A'}",
                "",
                ext.content,
                "",
                "---",
                "",
            ])

    content = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")

    return {
        "report": content,
        "file_count": len(file_paths),
        "output_path": output_path or None,
    }
