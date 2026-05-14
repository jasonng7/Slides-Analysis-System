from pathlib import Path


def convert_pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    deck_slug: str,
    dpi: int = 200,
) -> list[Path]:
    import fitz

    fitz.TOOLS.mupdf_display_errors(False)
    fitz.TOOLS.mupdf_display_warnings(False)

    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[Path] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_dir / f"{deck_slug}_slide_{page_index:03d}.png"
            pixmap.save(image_path)
            image_paths.append(image_path)

    return image_paths
