from tools.registry import tool
from core.summarizer import Summarizer
from core.extractor import PDFExtractor
from pathlib import Path

_extractor = PDFExtractor()
_summarizer = Summarizer()


@tool(
    name="summarize_pdf",
    description="Extract and summarize a PDF using OpenRouter.",
    file_path={"type": "string", "description": "Path to the PDF file"},
    max_tokens={"type": "integer", "description": "Max tokens for summary", "default": 1024},
)
def summarize_pdf(file_path: str, max_tokens: int = 1024) -> dict:
    extraction = _extractor.extract(Path(file_path))
    summary = _summarizer.summarize(extraction, max_tokens=max_tokens)
    return {
        "filename": extraction.filename,
        "summary": summary.summary,
        "model": summary.model,
        "tokens_used": summary.tokens_used,
    }


@tool(
    name="summarize_text",
    description="Summarize arbitrary text content via OpenRouter.",
    text={"type": "string", "description": "Text content to summarize"},
    max_tokens={"type": "integer", "description": "Max tokens for summary", "default": 512},
)
def summarize_text(text: str, max_tokens: int = 512) -> dict:
    from core.models import ExtractionResult
    extraction = ExtractionResult(
        source_path="inline",
        filename="inline.txt",
        content=text,
    )
    summary = _summarizer.summarize(extraction, max_tokens=max_tokens)
    return {
        "summary": summary.summary,
        "model": summary.model,
        "tokens_used": summary.tokens_used,
    }
