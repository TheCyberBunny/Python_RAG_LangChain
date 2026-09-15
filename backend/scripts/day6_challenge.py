"""
Day 6 challenge script: run the document-description chain against
real documents already loaded by the existing ingestion layer -
exactly the same pattern day6_demo.py used for tickets.

Run from backend\\, with Ollama running (`ollama serve`, or the
desktop app's background service) and the venv active:
    python -m scripts.day6_challenge
"""

from app.ai.chains import describe_document
from app.ingestion.document_loader import load_documents_from_folder


def main() -> None:
    documents = load_documents_from_folder("docs")
    for document in documents:
        description = describe_document(
            title=document.title,
            category=document.category.value,
            days_since_reviewed=document.days_since_reviewed(),
        )
        print(f"[Document {document.id}] {description}")


if __name__ == "__main__":
    main()