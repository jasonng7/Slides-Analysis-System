import re


def chunk_text(text: str, max_chars: int = 12000) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [f"Chunk 1 of 1\n\n{cleaned}"]

    blocks = re.split(r"\n{2,}", cleaned)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    last_heading = ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if _looks_like_heading(block):
            last_heading = block

        next_len = current_len + len(block) + 2
        if current and next_len > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [last_heading, block] if last_heading and last_heading != block else [block]
            current_len = sum(len(item) + 2 for item in current)
        else:
            current.append(block)
            current_len = next_len

    if current:
        chunks.append("\n\n".join(current).strip())

    total = len(chunks)
    return [f"Chunk {index} of {total}\n\n{chunk}" for index, chunk in enumerate(chunks, start=1)]


def _looks_like_heading(block: str) -> bool:
    first_line = block.splitlines()[0].strip()
    if len(first_line) > 120:
        return False
    return (
        first_line.startswith("#")
        or first_line.endswith(":")
        or first_line.isupper()
        or bool(re.match(r"^\d+(\.\d+)*\s+\S+", first_line))
    )
