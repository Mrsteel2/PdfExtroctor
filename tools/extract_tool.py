from pathlib import Path
from tools.registry import tool
from core.extractor import PDFExtractor

_extractor = PDFExtractor()


@tool(
    name="extract_pdf",
    description="Extract text content from a PDF file using MarkItDown.",
    file_path={"type": "string", "description": "Path to the PDF file"},
)
def extract_pdf(file_path: str) -> dict:
    result = _extractor.extract(Path(file_path))
    return {
        "filename": result.filename,
        "content": result.content,
        "page_count": result.page_count,
        "metadata": result.metadata,
        "extracted_at": result.extracted_at.isoformat(),
    }


@tool(
    name="extract_pdf_batch",
    description="Extract text from multiple PDF files.",
    file_paths={"type": "array", "items": {"type": "string"}, "description": "List of PDF paths"},
)
def extract_pdf_batch(file_paths: list[str]) -> list[dict]:
    results = _extractor.extract_batch([Path(p) for p in file_paths])
    return [
        {
            "filename": r.filename,
            "content": r.content,
            "page_count": r.page_count,
            "extracted_at": r.extracted_at.isoformat(),
        }
        for r in results
    ]
