import json
import re
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


DOC_LEVEL_FIELDS = ["doc_id", "title", "doc_type", "version", "effective_date",
                    "language", "owner", "file_type", "source_file"]

CLAUSE_RE = re.compile(r"^(\d+\.\d+)\b", re.MULTILINE)  # "3.2 Le client ..." -> "3.2"


def chunk_documents(documents):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    all_chunks = []

    for document in documents:

        for section in document["sections"]:

            text = section["text"].strip()

            if not text:
                continue

            chunks = text_splitter.split_text(text)

            for chunk in chunks:
                metadata = {k: document[k] for k in DOC_LEVEL_FIELDS if k in document}
                metadata["section_title"] = section["section_title"]
                metadata["clauses"] = CLAUSE_RE.findall(chunk)  

                all_chunks.append({"text": chunk, "metadata": metadata})

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
