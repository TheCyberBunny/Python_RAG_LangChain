"""
Day 8 playground: two small, throwaway checks that build intuition
before the real work begins - what RecursiveCharacterTextSplitter
actually does to text, and what an embedding actually looks like.
Neither function here touches the real document corpus or the Chroma
vector store; that's what `day8_demo.py` does.

Run from backend\\, with the venv active (the embedding check in Step
3 also needs Ollama running with `nomic-embed-text` pulled):
    python -m scripts.day8_playground
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings

EMBEDDING_MODEL = "nomic-embed-text"


def demo_splitter_mechanics() -> None:
	#Chunk size is the maximum, chunk overlap means adjacent chunks share up to that many characters
    splitter = RecursiveCharacterTextSplitter(chunk_size=70, chunk_overlap=10)

    text = (
        "Paragraph one covers onboarding steps for new engineers.\n\n"
        "Paragraph two covers on-call escalation procedures for incidents.\n\n"
        "Paragraph three covers the deploy pipeline stages in order."
    )

    chunks = splitter.split_text(text)
    for i, chunk in enumerate(chunks, start=1):
        print(f"--- Chunk {i} ({len(chunk)} chars) ---")
        print(chunk)



def demo_embedding_shape() -> None:
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vector = embeddings.embed_query("How do I roll back a failed deploy?")
    print(f"Vector length: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")


def main() -> None:
    print("=== RecursiveCharacterTextSplitter mechanics ===\n")
    demo_splitter_mechanics()

    print("\n=== OllamaEmbeddings shape check ===\n")
    demo_embedding_shape()


if __name__ == "__main__":
    main()
