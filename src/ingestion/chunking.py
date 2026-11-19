
import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(documents):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
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

                all_chunks.append({
                    "text": chunk,
                    "metadata": {
                        "doc_id": document["doc_id"],
                        "title": document["title"],
                        "file_type": document["file_type"],
                        "source_file": document["source_file"],
                        "section_title": section["section_title"]
                    }
                })

    return all_chunks


input_path = Path(r"C:\Users\LENOVO\E-com-assistant\data\processed\documents.json")

with open(input_path, "r", encoding="utf-8") as file:
    documents = json.load(file)


chunks = chunk_documents(documents)


output_path = Path(r"C:\Users\LENOVO\E-com-assistant\data\processed\chunks.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(chunks, file, ensure_ascii=False, indent=2)


print(f"Nombre de documents : {len(documents)}")
print(f"Nombre de chunks : {len(chunks)}")
