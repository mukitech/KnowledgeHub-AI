"""Prompt construction utilities for retrieval-augmented generation."""

_SEPARATOR = "─" * 60
_NO_ANSWER_MESSAGE = "I couldn't find relevant information in the uploaded documents to answer that question."

# System instruction governing answer synthesis, citation, and markdown output
_SYSTEM_INSTRUCTION = """\
You are KnowledgeHub AI, an enterprise knowledge assistant.

SYSTEM INSTRUCTIONS:
1. STRICT CONTEXT GROUNDING: Answer ONLY using the retrieved context provided below. Never hallucinate or rely on outside knowledge.
2. SYNTHESIZE ACROSS DOCUMENTS: When evidence comes from multiple documents or sections, synthesize the information into a unified, coherent response.
3. COMPARATIVE ANALYSIS: Compare documents, themes, or perspectives directly when requested by the user.
4. INLINE CITATIONS: Cite every important factual statement using bracketed source tags, e.g. [Source 1], [Source 2].
5. INSUFFICIENT EVIDENCE: If the retrieved context does not contain enough information to answer the question, state clearly:
   "{no_answer}"
6. CONCISE & MARKDOWN FORMATTED: Provide concise, clear, and well-structured answers using clean Markdown formatting (e.g. bold titles, bullet points, structured lists).
7. INTERNAL REASONING: Think step-by-step internally before generating the final answer. Output ONLY the final answer without revealing internal thinking.\
""".format(no_answer=_NO_ANSWER_MESSAGE)


def build_rag_prompt(
    query: str,
    retrieved_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """Build a context-grounded RAG prompt formatted for Groq LLM optimization.

    Args:
        query: User input question.
        retrieved_chunks: List of retrieved context chunk dictionaries.
        conversation_history: Optional list of prior conversation turn dicts.

    Returns:
        Formatted prompt string ready for LLM completion.
    """
    formatted_chunks: list[str] = []
    for index, chunk in enumerate(retrieved_chunks or [], start=1):
        if not isinstance(chunk, dict):
            continue
        chunk_text = chunk.get("chunk_text", "")
        if not (isinstance(chunk_text, str) and chunk_text.strip()):
            continue

        filename  = chunk.get("filename") or f"Document #{chunk.get('document_id', index)}"
        page_num  = chunk.get("page_number", 1) or 1
        chunk_idx = chunk.get("chunk_index", "?")
        raw_score = chunk.get("similarity_score", chunk.get("score", 0.0))
        score_val = f"{float(raw_score):.4f}" if raw_score else "N/A"

        source_block = (
            f"[Source {index}]\n"
            f"Filename: {filename}\n"
            f"Page: {page_num}\n"
            f"Chunk: {chunk_idx}\n"
            f"Similarity: {score_val}\n"
            f"Content:\n{chunk_text.strip()}"
        )
        formatted_chunks.append(source_block)

    numbered_context = "\n\n".join(formatted_chunks) if formatted_chunks else "No relevant context found."
    formatted_history = _format_history(conversation_history or [])

    return (
        f"{_SYSTEM_INSTRUCTION}\n\n"
        f"{_SEPARATOR}\n"
        f"Conversation History:\n\n{formatted_history}\n\n"
        f"{_SEPARATOR}\n"
        f"Retrieved Context:\n\n{numbered_context}\n\n"
        f"{_SEPARATOR}\n\n"
        f"Question:\n\n{query}\n\n"
        f"{_SEPARATOR}\n\n"
        f"Answer:"
    )


def _format_history(conversation_history: list[dict]) -> str:
    """Format prior messages for the prompt without leaking internal data."""
    messages: list[str] = []
    for message in conversation_history:
        if not isinstance(message, dict):
            continue
        role    = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            messages.append(f"{role.title()}: {content}")

    return "\n".join(messages) if messages else "No previous conversation."
