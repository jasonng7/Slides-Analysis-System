import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ingestion.convert_pdf_to_images import convert_pdf_to_images


def _find_soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def _render_preview_images(
    text_paths: list[Path],
    output_dir: Path,
    deck_slug: str,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[Path] = []
    font = ImageFont.load_default()

    for slide_index, text_path in enumerate(text_paths, start=1):
        image = Image.new("RGB", (1920, 1080), "white")
        draw = ImageDraw.Draw(image)
        title = f"Slide {slide_index}"
        draw.text((80, 70), title, fill="black", font=font)

        body = text_path.read_text(encoding="utf-8").strip() or "(No extractable text)"
        wrapped_lines = []
        for paragraph in body.splitlines():
            wrapped_lines.extend(textwrap.wrap(paragraph, width=110) or [""])

        y = 140
        for line in wrapped_lines[:45]:
            draw.text((80, y), line, fill="black", font=font)
            y += 22

        image_path = output_dir / f"{deck_slug}_slide_{slide_index:03d}.png"
        image.save(image_path)
        image_paths.append(image_path)

    return image_paths


def convert_pptx_to_images(
    pptx_path: Path,
    output_dir: Path,
    deck_slug: str,
    text_paths: list[Path],
    dpi: int = 200,
) -> tuple[list[Path], str]:
    soffice = _find_soffice()
    if not soffice:
        return _render_preview_images(text_paths, output_dir, deck_slug), "pillow_text_preview"

    with tempfile.TemporaryDirectory(prefix="slide_ingest_") as temp_dir:
        temp_path = Path(temp_dir)
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_path),
                str(pptx_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        pdf_path = temp_path / f"{pptx_path.stem}.pdf"
        if not pdf_path.exists():
            converted = list(temp_path.glob("*.pdf"))
            if not converted:
                raise RuntimeError(f"LibreOffice did not produce a PDF for {pptx_path}")
            pdf_path = converted[0]

        image_paths = convert_pdf_to_images(pdf_path, output_dir, deck_slug, dpi=dpi)
        return image_paths, "libreoffice_pdf_render"
