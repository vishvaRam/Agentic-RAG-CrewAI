from crewai_tools import RagTool
import os


def main():
    # Create a RAG tool with the specified embedding model configuration
    rag_tool = RagTool(
        config={
            "embedding_model": {
                "provider": "huggingface",
                "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}
            }
        }
    )
    
    # Add content from the Hugging Face blog post
    print("Adding content from Hugging Face blog...")
    try:
        # Fixed: The add() method now requires the URL as the first positional argument
        # and data_type as a keyword argument
        rag_tool.add("https://huggingface.co/blog/trl-vlm-alignment", data_type="web_page")
        print("Successfully added content from Hugging Face blog!")
    except Exception as e:
        print(f"Error adding content: {e}")
        return
    
    # Test the RAG tool with some sample queries
    test_queries = [
        "What is TRL VLM alignment about?",
        "What are the main concepts discussed in the blog post?",
        "How does vision-language model alignment work?",
        "What are the key benefits mentioned in the article?"
    ]
    
    print("\n" + "="*50)
    print("Testing RAG Tool with Sample Queries")
    print("="*50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        try:
            # Use the RAG tool to answer the query - use run() instead of _run()
            response = rag_tool.run(query)
            print(f"Answer: {response}")
        except Exception as e:
            print(f"Error processing query: {e}")
    
    # Interactive mode - allow user to ask custom questions
    print("\n" + "="*50)
    print("Interactive Mode - Ask your own questions!")
    print("Type 'quit' to exit")
    print("="*50)
    
    while True:
        user_query = input("\nYour question: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
            
        if not user_query:
            print("Please enter a valid question.")
            continue
            
        try:
            response = rag_tool.run(user_query)
            print(f"\nAnswer: {response}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
