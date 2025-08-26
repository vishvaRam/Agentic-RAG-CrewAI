from crewai_tools import RagTool

rag_tool = RagTool(
    config={
        "embedding_model": {
            "provider": "huggingface",
            "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}
        },
        "chunker": {
            "chunk_size": 1000,  # Larger chunks for better context
            "chunk_overlap": 100   # Reduced overlap to fix warning
        }
    },
)


