from pathlib import Path

import fitz
from docx import Document

from app.extraction import DOCX_MIME, PDF_MIME, _language, extract_document


def create_pdf(path: Path, pages: list[str]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_arabic_pdf_preserves_page_provenance(tmp_path):
    path = tmp_path / "notice.pdf"
    create_pdf(path, ["Commercial hearing notice dated 15 October 2026.", "The contract is active."])

    result = extract_document(path, PDF_MIME)

    assert result.status == "ready"
    assert [page.page_number for page in result.pages] == [1, 2]
    assert result.pages[0].language == "en"
    assert result.pages[1].language == "en"
    assert all(page.extraction_method == "text_layer" for page in result.pages)


def test_mixed_language_pdf_is_labeled_ar_en(tmp_path):
    assert _language("العقد Contract رقم 42") == "ar-en"


def test_arabic_text_is_labeled_ar():
    assert _language("إشعار جلسة تجارية") == "ar"


def test_image_only_pdf_requires_review_without_ocr(tmp_path):
    path = tmp_path / "scan.pdf"
    create_pdf(path, [""])

    result = extract_document(path, PDF_MIME)

    assert result.status == "needs_review"
    assert result.pages[0].quality == "poor"
    assert result.pages[0].extraction_method == "text_layer"
    assert result.review_reasons == ["Page 1 has insufficient extracted text"]


def test_docx_text_is_extracted_as_page_one(tmp_path):
    path = tmp_path / "contract.docx"
    document = Document()
    document.add_paragraph("هذا عقد تجاري صالح مع شركة التوريد.")
    document.save(path)

    result = extract_document(path, DOCX_MIME)

    assert result.status == "ready"
    assert result.pages[0].page_number == 1
    assert result.pages[0].language == "ar"
    assert "عقد تجاري" in result.pages[0].text


def test_ocr_adapter_can_supply_text_for_empty_page(tmp_path):
    path = tmp_path / "scan.pdf"
    create_pdf(path, [""])

    class FakeOCR:
        def extract(self, _path, _page_number):
            return "إشعار جلسة تجارية بتاريخ 15 أكتوبر 2026"

    result = extract_document(path, PDF_MIME, FakeOCR())

    assert result.status == "ready"
    assert result.pages[0].extraction_method == "ocr"
    assert result.pages[0].language == "ar"