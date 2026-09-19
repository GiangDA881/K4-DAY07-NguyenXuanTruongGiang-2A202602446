from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Knowledge base is empty. No context available to answer the question."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "No relevant information found in the knowledge base."

        context_blocks = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", r.get("id", f"doc_{i}"))
            content = r.get("content", "").strip()
            context_blocks.append(f"[{i}] (Source: {source})\n{content}")

        context_str = "\n\n".join(context_blocks)
        prompt = (
            f"You are a helpful knowledge assistant. Answer the question based ONLY on the provided context.\n"
            f"If the context does not contain enough information, state that clearly. Cite sources using [1], [2], etc.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )
        return self.llm_fn(prompt)
