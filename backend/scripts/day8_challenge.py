"""
Day 8 challenge script: query the already-persisted Chroma vector
store built by day8_demo.py - without ever rebuilding it.

Run from backend\\, AFTER scripts\\day8_demo.py has already been run at
least once (so chroma_db\\ exists), with Ollama running and
`nomic-embed-text` pulled:
    python -m scripts.day8_challenge
"""

from app.rag.vector_store import search_documents


def main() -> None:
    query = "How do I get set up on my first day?"

    print("=== Unfiltered search ===\n")
    results = search_documents(query, k=3)
    for i, result in enumerate(results, start=1):
        print(f"--- Match {i} ---")
        print(f"Title: {result.metadata['title']} ({result.metadata['category']})")
        print(f"Chunk: {result.page_content!r}")

    print("\n=== Filtered to category='Onboarding' ===\n")
    filtered_results = search_documents(query, k=3, category="Onboarding")
    for i, result in enumerate(filtered_results, start=1):
        print(f"--- Match {i} ---")
        print(f"Title: {result.metadata['title']} ({result.metadata['category']})")
        print(f"Chunk: {result.page_content!r}")


if __name__ == "__main__":
    main()