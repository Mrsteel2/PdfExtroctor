from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExtractionResult:
    source_path: str
    filename: str
    content: str
    content_type: str = "text/markdown"
    extracted_at: datetime = field(default_factory=datetime.now)
    page_count: Optional[int] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class SummaryResult:
    extraction: ExtractionResult
    summary: str
    model: str
    tokens_used: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Report:
    title: str
    summary: str
    sections: list[dict]
    generated_at: datetime = field(default_factory=datetime.now)
    recipients: list[str] = field(default_factory=list)
    attachment_path: Optional[str] = None
