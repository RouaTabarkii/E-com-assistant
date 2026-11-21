import json
import re
from collections import Counter
from pathlib import Path
import yaml
from docx import Document
from pypdf import PdfReader

def read_front_matter(file_path):
    text = Path(file_path).read_text(encoding="utf-8")

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    metadata = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()

    if "effective_date" in metadata:
        metadata["effective_date"] = str(metadata["effective_date"])

    return metadata, body


def split_sections(body):
    sections = []
    current = None

    for line in body.split("\n"):
        if line.startswith("## "):
            if current is not None:
                sections.append(current)
            current = {"section_title": line[3:].strip(), "lines": []}
        elif current is not None:
            if line.strip():
                current["lines"].append(line.strip())

    if current is not None:
        sections.append(current)

    return [
        {"section_title": s["section_title"], "text": "\n".join(s["lines"])}
        for s in sections
    ]


def load_markdown(file_path):
    path = Path(file_path)
    meta, body = read_front_matter(path)
    sections = split_sections(body)

    document = dict(meta)
    document.setdefault("doc_id", path.stem)
    document.setdefault("title", path.stem)
    document["source_file"] = path.name
    document["file_type"] = "md"
    document["sections"] = sections
    return document

def load_docx(file_path):
    path = Path(file_path)
    doc = Document(path)

    title = None
    sections = []
    current = None

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style = p.style.name.lower()

        if style in ("title", "titre", "heading 1", "titre 1"):
            title = title or text
        elif style in ("heading 2", "titre 2"):
            if current is not None:
                sections.append(current)
            current = {"section_title": text, "lines": []}
        elif current is not None:
            current["lines"].append(text)

    if current is not None:
        sections.append(current)

    return {
        "doc_id": path.stem,
        "title": title or path.stem,
        "source_file": path.name,
        "file_type": "docx",
        "sections": [
            {"section_title": s["section_title"], "text": "\n".join(s["lines"])}
            for s in sections
        ],
    }



SECTION_RE = re.compile(r"^\d+\.\s+\S")  # "1. Principe"
PAGE_NUM_RE = re.compile(r"^(page\s*)?\d+(\s*/\s*\d+)?$", re.IGNORECASE)


def load_pdf(file_path):
    path = Path(file_path)
    reader = PdfReader(path)

    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append([l.strip() for l in text.split("\n") if l.strip()])

    counts = Counter(l for lines in pages for l in set(lines))
    repeated = {l for l, c in counts.items() if len(pages) > 1 and c == len(pages)}
    lines = [
        l for page_lines in pages for l in page_lines
        if l not in repeated and not PAGE_NUM_RE.match(l)
    ]

    if not lines:
        print(f"[WARN] {path.name} : aucun texte extractible (PDF scanné ?)")

    sections = []
    current = None
    for line in lines:
        if SECTION_RE.match(line):
            if current is not None:
                sections.append(current)
            current = {"section_title": line, "lines": []}
        elif current is not None:
            current["lines"].append(line)
    if current is not None:
        sections.append(current)

    return {
        "doc_id": path.stem,
        "title": lines[0] if lines else path.stem,
        "source_file": path.name,
        "file_type": "pdf",
        "sections": [
            {"section_title": s["section_title"], "text": "\n".join(s["lines"])}
            for s in sections
        ],
    }


def load_document(file_path):
    """Regarde l'extension et lance la bonne fonction."""
    ext = Path(file_path).suffix.lower()

    if ext == ".md":
        return load_markdown(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext == ".pdf":
        return load_pdf(file_path)
    else:
        print(f"[SKIP] {Path(file_path).name} : format non pris en charge")
        return None


def load_all_documents(policies_dir):
    documents = []
    for path in sorted(Path(policies_dir).rglob("*")):
        if not path.is_file():
            continue
        if path.name.lower().startswith("readme"):
            continue  # documentation du corpus, pas une politique : ne pas l'indexer
        doc = load_document(path)
        if doc is not None:
            documents.append(doc)
            print(f"[OK] {path.name}")
    return documents


def save_documents(documents, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(documents)} documents sauvegardés dans {output_path}")


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]

    docs = load_all_documents(ROOT / "data" / "policies")
    save_documents(docs, ROOT / "data" / "processed" / "documents.json")

