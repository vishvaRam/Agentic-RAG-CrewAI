from crewai_tools import RagTool

rag_tool = RagTool(
    config={
        "embedding_model": {
            "provider": "huggingface",
            "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}
        }
    }
)
