from pathlib import Path


def extract_text_from_pdf(pdf_path: Path, output_dir: Path, deck_slug: str) -> list[Path]:
    import fitz

    fitz.TOOLS.mupdf_display_errors(False)
    fitz.TOOLS.mupdf_display_warnings(False)

    output_dir.mkdir(parents=True, exist_ok=True)
    text_paths: list[Path] = []

    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            text_path = output_dir / f"{deck_slug}_slide_{page_index:03d}.txt"
            text_path.write_text(text + ("\n" if text else ""), encoding="utf-8")
            text_paths.append(text_path)

    return text_paths
