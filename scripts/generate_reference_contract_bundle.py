import argparse
import hashlib
import html
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "fixtures" / "reference" / "contracts" / "source" / "bundle.json"
OUTPUT_DIR = ROOT / "fixtures" / "reference" / "contracts"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

NAVY = colors.HexColor("#18324A")
BLUE = colors.HexColor("#23658B")
LIGHT_BLUE = colors.HexColor("#EAF3F8")
LIGHT_GRAY = colors.HexColor("#F3F5F7")
MID_GRAY = colors.HexColor("#65717C")
DARK = colors.HexColor("#1C2730")
WHITE = colors.white


class DeterministicCanvas(canvas.Canvas):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["invariant"] = 1
        super().__init__(*args, **kwargs)
        self.setAuthor("Acme Cloud")
        self.setCreator("Enact reference contract generator")
        self.setProducer("Enact deterministic PDF generator")
        self.setSubject("Development reference contract")


class AccentRule(Flowable):
    def __init__(self, width: float) -> None:
        super().__init__()
        self.width = width
        self.height = 5

    def draw(self) -> None:
        self.canv.setFillColor(BLUE)
        self.canv.roundRect(0, 0, self.width, self.height, 2.5, fill=1, stroke=0)


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ContractTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "subtitle": ParagraphStyle(
            "ContractSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=BLUE,
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "ContractSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "ContractBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.2,
            textColor=DARK,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "ContractSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10.2,
            textColor=DARK,
        ),
        "small_bold": ParagraphStyle(
            "ContractSmallBold",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=10.2,
            textColor=NAVY,
        ),
        "table_header": ParagraphStyle(
            "ContractTableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=10.2,
            textColor=WHITE,
        ),
        "meta_label": ParagraphStyle(
            "MetadataLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=MID_GRAY,
        ),
        "meta_value": ParagraphStyle(
            "MetadataValue",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.5,
            textColor=DARK,
        ),
        "signature": ParagraphStyle(
            "Signature",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=11,
            textColor=DARK,
        ),
        "center_small": ParagraphStyle(
            "CenterSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=MID_GRAY,
        ),
    }


def safe(value: Any) -> str:
    return html.escape(str(value), quote=False)


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(safe(text), style)


def page_decoration(document: dict[str, Any]):
    def decorate(pdf: canvas.Canvas, doc: BaseDocTemplate) -> None:
        width, height = LETTER
        pdf.saveState()
        pdf.setFillColor(NAVY)
        pdf.rect(0, height - 0.32 * inch, width, 0.32 * inch, fill=1, stroke=0)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.setFillColor(WHITE)
        pdf.drawString(0.65 * inch, height - 0.21 * inch, "ACME CLOUD")
        pdf.setFont("Helvetica", 7.5)
        pdf.drawRightString(
            width - 0.65 * inch,
            height - 0.21 * inch,
            f"{document['document_id']}  |  Version {document['version']}",
        )
        pdf.setStrokeColor(colors.HexColor("#C9D2D9"))
        pdf.line(0.65 * inch, 0.52 * inch, width - 0.65 * inch, 0.52 * inch)
        pdf.setFillColor(MID_GRAY)
        pdf.setFont("Helvetica", 7.2)
        pdf.drawString(0.65 * inch, 0.34 * inch, "Development reference contract")
        pdf.drawRightString(width - 0.65 * inch, 0.34 * inch, f"Page {doc.page}")
        pdf.restoreState()

    return decorate


def metadata_table(document: dict[str, Any], style_map: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [
            paragraph("DOCUMENT ID", style_map["meta_label"]),
            paragraph(document["document_id"], style_map["meta_value"]),
            paragraph("VERSION", style_map["meta_label"]),
            paragraph(document["version"], style_map["meta_value"]),
        ],
        [
            paragraph("EFFECTIVE DATE", style_map["meta_label"]),
            paragraph(document["effective_date"], style_map["meta_value"]),
            paragraph("EXECUTION DATE", style_map["meta_label"]),
            paragraph(
                document.get("execution_date") or "Not separately executed", style_map["meta_value"]
            ),
        ],
    ]
    table = Table(rows, colWidths=[1.05 * inch, 2.1 * inch, 1.05 * inch, 2.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D7DEE3")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7DEE3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def content_table(
    table_data: dict[str, Any], style_map: dict[str, ParagraphStyle], available_width: float
) -> Table:
    headers = [paragraph(value, style_map["table_header"]) for value in table_data["headers"]]
    rows = [[paragraph(value, style_map["small"]) for value in row] for row in table_data["rows"]]
    widths = [available_width * fraction for fraction in table_data["widths"]]
    table = Table([headers, *rows], colWidths=widths, repeatRows=1, splitByRow=1)
    commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BCC7CF")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D4DBE0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index in range(1, len(rows) + 1):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), LIGHT_BLUE))
    table.setStyle(TableStyle(commands))
    return table


def signature_table(
    signatures: list[list[str]], style_map: dict[str, ParagraphStyle], available_width: float
) -> Table:
    cells = []
    for entity, name, title, date in signatures:
        content = (
            f"<b>{safe(entity)}</b><br/><br/>"
            f"/s/ {safe(name)}<br/>"
            f"{safe(title)}<br/>"
            f"Date: {safe(date)}"
        )
        cells.append(Paragraph(content, style_map["signature"]))
    table = Table([cells], colWidths=[available_width / len(cells)] * len(cells))
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BCC7CF")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#BCC7CF")),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def build_document(document: dict[str, Any], destination: Path) -> None:
    style_map = styles()
    page_width, page_height = LETTER
    left_margin = 0.65 * inch
    right_margin = 0.65 * inch
    top_margin = 0.62 * inch
    bottom_margin = 0.7 * inch
    available_width = page_width - left_margin - right_margin

    pdf = BaseDocTemplate(
        str(destination),
        pagesize=LETTER,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title=document["title"],
        author="Acme Cloud",
        subject="Development reference contract",
        pageCompression=1,
    )
    frame = Frame(
        left_margin,
        bottom_margin,
        available_width,
        page_height - top_margin - bottom_margin,
        id="contract",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    pdf.addPageTemplates(
        [PageTemplate(id="contract", frames=[frame], onPageEnd=page_decoration(document))]
    )

    story: list[Flowable] = [
        Spacer(1, 0.16 * inch),
        paragraph(document["title"], style_map["title"]),
        paragraph(document["subtitle"], style_map["subtitle"]),
        AccentRule(available_width),
        Spacer(1, 0.17 * inch),
        metadata_table(document, style_map),
        Spacer(1, 0.2 * inch),
        paragraph(document["intro"], style_map["body"]),
    ]

    for section in document["sections"]:
        section_content: list[Flowable] = [
            paragraph(f"{section['id']}  {section['title']}", style_map["section"])
        ]

        if section.get("table"):
            section_content.extend(
                [
                    content_table(section["table"], style_map, available_width),
                    Spacer(1, 0.08 * inch),
                ]
            )

        for text in section.get("paragraphs", []):
            section_content.append(paragraph(text, style_map["body"]))

        if section.get("signatures"):
            section_content.extend(
                [
                    Spacer(1, 0.08 * inch),
                    signature_table(section["signatures"], style_map, available_width),
                ]
            )

        story.append(KeepTogether(section_content))

    pdf.build(story, canvasmaker=DeterministicCanvas)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_pdf_text(path: Path) -> str:
    reader = PdfReader(path)
    return " ".join(" ".join(page.extract_text().split()) for page in reader.pages)


def validate_document(document: dict[str, Any], path: Path) -> int:
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError(f"Generated PDF must not be encrypted: {path.name}")
    if not reader.pages:
        raise ValueError(f"Generated PDF has no pages: {path.name}")

    extracted = normalized_pdf_text(path)
    for section in document["sections"]:
        if section["id"] not in extracted:
            raise ValueError(f"Missing clause identifier {section['id']} in {path.name}")

    required_phrases = {
        "OF-REDWOOD-2027-001": [
            "USD 163,200",
            "20 TB monthly data processing capacity",
            "initial response within 30 minutes",
            "USD 12,000",
        ],
        "MSA-2026-01": ["the more specific negotiated term in the Order Form controls"],
        "PS-ENTERPRISE-2026-10": ["normally includes 10 TB"],
        "SS-PREMIUM-2026-10": ["1 hour", "2 business hours"],
        "SOW-REDWOOD-2027-001": [
            "Within 5 business days after the effective date",
            "Within 30 calendar days after kickoff",
            "when kickoff is recorded as completed",
        ],
        "AMD-REDWOOD-2027-001": [
            "450 seats",
            "USD 18,147.95",
            "35 TB aggregate monthly data processing capacity",
            "shared across the two production workspaces",
            "USD 450 per TB",
            "does not modify the Enterprise platform subscription",
        ],
    }
    for phrase in required_phrases[document["document_id"]]:
        if phrase not in extracted:
            raise ValueError(f"Missing required phrase {phrase!r} in {path.name}")

    forbidden_phrases = [
        "20 TB allowance is pooled",
        "40 TB total",
        "approval required",
        "exception approval",
    ]
    for phrase in forbidden_phrases:
        if phrase.lower() in extracted.lower():
            raise ValueError(f"Forbidden resolution or policy phrase {phrase!r} in {path.name}")

    return len(reader.pages)


def generate_bundle() -> None:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    documents = source["documents"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with (
        tempfile.TemporaryDirectory(prefix="enact-contracts-first-") as first_dir_name,
        tempfile.TemporaryDirectory(prefix="enact-contracts-second-") as second_dir_name,
    ):
        first_dir = Path(first_dir_name)
        second_dir = Path(second_dir_name)
        for document in documents:
            build_document(document, first_dir / document["filename"])
            build_document(document, second_dir / document["filename"])

        manifest_documents = []
        for document in documents:
            first = first_dir / document["filename"]
            second = second_dir / document["filename"]
            first_hash = file_hash(first)
            second_hash = file_hash(second)
            if first_hash != second_hash:
                raise RuntimeError(f"PDF generation is not deterministic: {document['filename']}")

            page_count = validate_document(document, first)
            destination = OUTPUT_DIR / document["filename"]
            shutil.copyfile(first, destination)
            manifest_documents.append(
                {
                    "filename": document["filename"],
                    "document_id": document["document_id"],
                    "document_type": document["document_type"],
                    "version": document["version"],
                    "effective_date": document["effective_date"],
                    "page_count": page_count,
                    "sha256": first_hash,
                }
            )

    manifest = {
        "schema_version": "1.0",
        "bundle_id": source["bundle_id"],
        "bundle_title": source["bundle_title"],
        "source": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": file_hash(SOURCE_PATH),
        "documents": manifest_documents,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Generated and validated {len(documents)} PDFs in {OUTPUT_DIR.relative_to(ROOT)}")
    for item in manifest_documents:
        print(f"- {item['filename']}: {item['page_count']} pages, sha256={item['sha256']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Enact reference contract bundle.")
    return parser.parse_args()


if __name__ == "__main__":
    parse_args()
    generate_bundle()
