import json
import re
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOC_LEVEL_FIELDS = ["doc_id", "title", "doc_type", "version", "effective_date",
                    "language", "owner", "file_type", "source_file"]

CLAUSE_RE = re.compile(r"^(\d+\.\d+)\b", re.MULTILINE)  
SECTION_NUM_RE = re.compile(r"^(\d+)\.\s+(.*)$")         


def chunk_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    all_chunks = []

    for document in documents:
        section_counter = 1

        for section in document["sections"]:

            text = section["text"].strip()

            if not text:
                continue

            chunks = text_splitter.split_text(text)
            m = SECTION_NUM_RE.match(section["section_title"])
            section_number = m.group(1) if m else str(section_counter)
            section_label = m.group(2) if m else section["section_title"]
            for part, chunk in enumerate(chunks, start=1):
                metadata = {k: document[k] for k in DOC_LEVEL_FIELDS if k in document}
                metadata["section_title"] = section["section_title"]
                metadata["section_number"] = section_number
                metadata["clauses"] = CLAUSE_RE.findall(chunk) 
                metadata["part"] = part         
                metadata["n_parts"] = len(chunks)
                suffix = f".{part}" if len(chunks) > 1 else ""
                metadata["chunk_id"] = f"{document['doc_id']}#s{section_number}{suffix}"
                metadata["citation"] = (
                    f"[{document['doc_id']} v{document.get('version', '?')}, "
                    f"§ {section_number} {section_label}]"
                )

                all_chunks.append({"text": chunk, "metadata": metadata})
            section_counter += 1

    return all_chunks


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    input_path = ROOT / "data" / "processed" / "documents.json"
    output_path = ROOT / "data" / "processed" / "chunks.json"

    with open(input_path, "r", encoding="utf-8") as file:
        documents = json.load(file)

    chunks = chunk_documents(documents)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    print(f"Nombre de documents : {len(documents)}")
    print(f"Nombre de chunks : {len(chunks)}")
