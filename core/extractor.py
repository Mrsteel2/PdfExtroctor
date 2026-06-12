from pathlib import Path
from typing import Optional
import logging

from core.models import ExtractionResult

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".xlsx", ".xls", ".html", ".htm",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff",
    ".txt", ".csv", ".json", ".xml",
}


class PDFExtractor:
    def __init__(self):
        self._converter = None

    @property
    def converter(self):
        if self._converter is None:
            from markitdown import MarkItDown
            self._converter = MarkItDown()
        return self._converter

    def extract(self, file_path: str | Path) -> ExtractionResult:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.name}")

        logger.info("Extracting %s", path.name)
        result = self.converter.convert(str(path))

        metadata = {}
        if path.suffix.lower() == ".pdf":
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(str(path))
                metadata["page_count"] = len(reader.pages)
                if reader.metadata:
                    for k, v in reader.metadata.items():
                        key = k.removeprefix("/")
                        metadata[key] = str(v)
            except ImportError:
                pass

        return ExtractionResult(
            source_path=str(path),
            filename=path.name,
            content=result.text_content if hasattr(result, "text_content") else str(result),
            content_type="text/markdown",
            page_count=metadata.get("page_count"),
            metadata=metadata,
        )

    def extract_batch(self, file_paths: list[str | Path]) -> list[ExtractionResult]:
        return [self.extract(p) for p in file_paths]
