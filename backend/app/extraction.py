from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import re

import fitz
from docx import Document
from PIL import Image
import pytesseract


MIN_USABLE_CHARACTERS = 20
PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class OCRAdapter(Protocol):
    def extract(self, path: Path, page_number: int) -> str | None:
        """Return OCR text for a one-based page, or None when unavailable."""


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    language: str
    extraction_method: str
    quality: str


@dataclass(frozen=True)
class ExtractionResult:
    pages: list[ExtractedPage]
    status: str
    review_reasons: list[str]


class TesseractOCR:
    def extract(self, path: Path, page_number: int) -> str | None:
        with fitz.open(path) as document:
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        return pytesseract.image_to_string(image, lang="ara+eng")


def _language(text: str) -> str:
    has_arabic = bool(re.search(r"[\u0600-\u06ff]", text))
    has_latin = bool(re.search(r"[A-Za-z]", text))
    if has_arabic and has_latin:
        return "ar-en"
    if has_arabic:
        return "ar"
    if has_latin:
        return "en"
    return "unknown"


def _page_quality(text: str) -> str:
    return "usable" if len(text.strip()) >= MIN_USABLE_CHARACTERS else "poor"


def _extract_pdf(path: Path, ocr: OCRAdapter | None) -> ExtractionResult:
    pages: list[ExtractedPage] = []
    review_reasons: list[str] = []
    with fitz.open(path) as document:
        for index, pdf_page in enumerate(document):
            text = pdf_page.get_text("text").strip()
            method = "text_layer"
            quality = _page_quality(text)
            if quality == "poor" and ocr is not None:
                ocr_text = (ocr.extract(path, index + 1) or "").strip()
                if ocr_text:
                    text = ocr_text
                    method = "ocr"
                    quality = _page_quality(text)
            if quality == "poor":
                review_reasons.append(f"Page {index + 1} has insufficient extracted text")
            pages.append(ExtractedPage(index + 1, text, _language(text), method, quality))
    status = "ready" if pages and not review_reasons else "needs_review"
    if not pages:
        review_reasons.append("Document contains no pages")
    return ExtractionResult(pages, status, review_reasons)


def _extract_docx(path: Path) -> ExtractionResult:
    document = Document(path)
    text = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())
    quality = _page_quality(text)
    reasons = [] if quality == "usable" else ["DOCX contains insufficient extracted text"]
    return ExtractionResult(
        [ExtractedPage(1, text, _language(text), "text_layer", quality)] if text else [],
        "ready" if quality == "usable" else "needs_review",
        reasons,
    )


def extract_document(path: Path, mime_type: str, ocr: OCRAdapter | None = None) -> ExtractionResult:
    if ocr is None and mime_type == PDF_MIME:
        try:
            pytesseract.get_tesseract_version()
            ocr = TesseractOCR()
        except (pytesseract.TesseractNotFoundError, RuntimeError):
            ocr = None
    if mime_type == PDF_MIME:
        return _extract_pdf(path, ocr)
    if mime_type == DOCX_MIME:
        return _extract_docx(path)
    raise ValueError(f"Unsupported extraction type: {mime_type}")