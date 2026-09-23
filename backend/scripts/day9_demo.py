"""
Day 9 demo script: wrap the already-persisted Chroma store as
similarity and MMR retrievers, and format their results into a
citation-ready context string.

Run from backend\\, AFTER scripts\\day8_demo.py has already been run at
least once (so chroma_db\\ exists), with Ollama running and
`nomic-embed-text` pulled:
    python -m scripts.day9_demo
"""

from app.rag.retriever import (
    format_retrieved_context,
    get_diverse_retriever,
    get_similarity_retriever,
)


def main() -> None:
    query = "What should I do first when a P1 incident starts?"

    print("=== Similarity retriever ===\n")
    similarity_retriever = get_similarity_retriever(k=3)
    similarity_results = similarity_retriever.invoke(query)
    for i, result in enumerate(similarity_results, start=1):
        print(f"--- Match {i}: {result.metadata['title']} ({result.metadata['category']}) ---")

    print("\nFormatted context (ready to hand to an LLM tomorrow):\n")
    print(format_retrieved_context(similarity_results))

    print("\n=== MMR retriever (same query, re-ranked for diversity) ===\n")
    diverse_retriever = get_diverse_retriever(k=3)
    diverse_results = diverse_retriever.invoke(query)
    for i, result in enumerate(diverse_results, start=1):
        print(f"--- Match {i}: {result.metadata['title']} ({result.metadata['category']}) ---")


if __name__ == "__main__":
    main()