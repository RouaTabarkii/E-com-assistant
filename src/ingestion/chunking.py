import json
import re
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Métadonnées du document recopiées sur chaque chunk (elles étaient perdues auparavant,
# ce qui laissait version / effective_date / doc_type / language vides dans Qdrant).
DOC_LEVEL_FIELDS = ["doc_id", "title", "doc_type", "version", "effective_date",
                    "language", "owner", "file_type", "source_file"]

CLAUSE_RE = re.compile(r"^(\d+\.\d+)\b", re.MULTILINE)  # "3.2 Le client ..." -> "3.2"
SECTION_NUM_RE = re.compile(r"^(\d+)\.\s+(.*)$")          # "3. Colis perdu" -> ("3", "Colis perdu")


def chunk_documents(documents):
    # Les sections de nos politiques font < ~520 caractères : 800 => un chunk par section,
    # ce qui rend les citations [doc, section] précises. Le découpage ne s'applique
    # qu'aux sections plus longues (PDF, DOCX).
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

            # "3. Compensation en cas de retard" -> numéro "3", intitulé "Compensation en cas de retard"
            m = SECTION_NUM_RE.match(section["section_title"])
            section_number = m.group(1) if m else str(section_counter)
            section_label = m.group(2) if m else section["section_title"]

            for part, chunk in enumerate(chunks, start=1):
                metadata = {k: document[k] for k in DOC_LEVEL_FIELDS if k in document}
                metadata["section_title"] = section["section_title"]
                metadata["section_number"] = section_number
                metadata["clauses"] = CLAUSE_RE.findall(chunk)  # cibles de citation (§ 3.2)
                metadata["part"] = part          # position du chunk dans sa section
                metadata["n_parts"] = len(chunks)
                # Identifiant STABLE : ne dépend ni de l'ordre des fichiers ni des autres documents.
                suffix = f".{part}" if len(chunks) > 1 else ""
                metadata["chunk_id"] = f"{document['doc_id']}#s{section_number}{suffix}"
                # Étiquette de citation prête à afficher dans la réponse de l'agent.
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
