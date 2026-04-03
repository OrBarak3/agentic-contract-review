from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from contract_review_langgraph.models import ClauseSegment


class UnsupportedDocumentError(RuntimeError):
    """Raised when the parser can identify the file but cannot safely read it."""


def compute_file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_contract(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8"), "text"
    if suffix == ".docx":
        document = Document(path)
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n\n".join(paragraphs), "docx"
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            page_text = (page.extract_text() or "").strip()
            if page_text:
                pages.append(page_text)
        text = "\n\n".join(pages).strip()
        if not text:
            raise UnsupportedDocumentError("pdf_has_no_selectable_text")
        return text, "pdf"
    raise UnsupportedDocumentError(f"unsupported_extension:{suffix or 'none'}")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _candidate_title(block: str) -> str:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return "Untitled Clause"
    first = lines[0]
    if len(first) <= 80:
        return first
    return first[:77].rstrip() + "..."


def chunk_into_clauses(text: str) -> list[ClauseSegment]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    blocks = [block.strip() for block in re.split(r"\n\s*\n", normalized) if block.strip()]
    clauses: list[ClauseSegment] = []
    cursor = 0
    for index, block in enumerate(blocks, start=1):
        start = normalized.find(block, cursor)
        if start == -1:
            start = cursor
        end = start + len(block)
        cursor = end
        clauses.append(
            ClauseSegment(
                clause_id=f"clause-{index:03d}",
                title=_candidate_title(block),
                text=block,
                start_char=start,
                end_char=end,
            )
        )
    return clauses

