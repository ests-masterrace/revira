import os
import re
import ollama
from pypdf import PdfReader

# import easyocr

EMBED_MODEL = "nomic-embed-text"


# def read_png(path, delim="|") -> str:
#     reader = easyocr.Reader(["en"])
#     result = reader.readtext(path)
#     text = [item[1] for item in result]
#     return delim.join(text)


# TODO: Handle image based PDFs
def read_pdf(path, delim: str = "#") -> str:
    text: str = ""
    reader = PdfReader(path)
    i = 1
    for page in reader.pages:
        text += f"{20 * delim} START PAGE {i} {20 * delim}\n\n"
        text += page.extract_text()
        text += f"\n\n{20 * delim} END PAGE {i} {20 * delim}\n\n"
        i += 1
    return text


def read_txtf(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def read_txtd(path) -> dict[str, str]:
    text_contents: dict[str, str] = {}
    directory = os.path.join(path)

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            text_contents[filename] = read_txtf(file_path)

    return text_contents


def chunk_splitter(text, chunk_size=100) -> list[str]:
    words = re.findall(r"\S+", text)

    chunks: list[str] = []
    current_chunk = []
    word_count = 0

    for word in words:
        current_chunk.append(word)
        word_count += 1

        if word_count >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            word_count = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def get_embedding(chunks: list[str]):
    embeds = ollama.embed(model=EMBED_MODEL, input=chunks)
    return embeds.get("embeddings", [])
