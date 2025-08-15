import os
import json
from typing import Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field, PrivateAttr
from crewai.tools import BaseTool
from crewai_tools.tools import TavilySearchTool
from tools.rag_tool import rag_tool

# Load environment variables from .env file
load_dotenv()

class SearchAndEmbeddingInput(BaseModel):
    """Input schema for SearchAndEmbedding tool."""
    query: str = Field(..., description="The search query to find relevant information")

class SearchAndEmbeddingTool(BaseTool):
    """
    Custom CrewAI tool that searches the web using Tavily and adds the results to RAG tool.
    This tool combines web search capabilities with RAG embedding for enhanced information retrieval.
    """
    
    name: str = "Search and Embedding Tool"
    description: str = (
        "Searches the web for information using Tavily search and automatically "
        "adds the found URLs to the RAG tool for embedding and future retrieval. "
        "Returns both search results and confirmation of RAG embedding."
    )
    args_schema: Type[BaseModel] = SearchAndEmbeddingInput
    
    # Use PrivateAttr for internal tools
    _tavily_tool: TavilySearchTool = PrivateAttr()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Verify API key is loaded
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY not found in environment. "
                "Please check your .env file or set the environment variable."
            )
        
        # Initialize Tavily search tool with API key using private attribute
        self._tavily_tool = TavilySearchTool(
            api_key=api_key,
            search_depth="basic",
            max_results=5,
            include_raw_content=False
        )
    
    def _run(self, query: str) -> str:
        """
        Execute the search and embedding process.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted string with search results and embedding status
        """
        try:
            # Perform search using Tavily
            print(f"🔍 Searching for: {query}")
            search_result = self._tavily_tool.run(query)
            
            # Parse the search result (it comes as a string representation of JSON)
            try:
                if isinstance(search_result, str):
                    # Clean up the string and parse as JSON
                    search_data = json.loads(search_result)
                else:
                    search_data = search_result
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing search results: {e}")
                return f"Error: Could not parse search results for query '{query}'"
            
            # Extract URLs and relevant information
            if not isinstance(search_data, dict) or "results" not in search_data:
                return f"Error: Unexpected search result format for query '{query}'"
            
            results = search_data.get("results", [])
            if not results:
                return f"No search results found for query '{query}'"
            
            # Process each result and add to RAG
            embedded_urls = []
            failed_urls = []
            search_summary = []
            
            print(f"📚 Processing {len(results)} search results...")
            
            for i, result in enumerate(results, 1):
                url = result.get("url", "")
                title = result.get("title", "Unknown Title")
                content_preview = result.get("content", "")[:200] + "..."
                score = result.get("score", 0)
                
                # Add to search summary
                search_summary.append({
                    "rank": i,
                    "title": title,
                    "url": url,
                    "score": score,
                    "preview": content_preview
                })
                
                # Try to add URL to RAG tool
                if url:
                    try:
                        print(f"  📄 Adding to RAG: {title[:50]}...")
                        rag_tool.add(url, data_type="web_page")
                        embedded_urls.append({"url": url, "title": title})
                        print(f"  ✅ Successfully embedded: {url}")
                    except Exception as e:
                        print(f"  ❌ Failed to embed {url}: {str(e)}")
                        failed_urls.append({"url": url, "title": title, "error": str(e)})
            
            # Format response
            response_parts = [
                f"🔍 SEARCH RESULTS FOR: '{query}'",
                f"Found {len(results)} results, processed {len(embedded_urls + failed_urls)}",
                "",
                "📋 SEARCH SUMMARY:"
            ]
            
            for item in search_summary:
                response_parts.append(
                    f"{item['rank']}. {item['title']}\n"
                    f"   URL: {item['url']}\n"
                    f"   Score: {item['score']:.3f}\n"
                    f"   Preview: {item['preview']}\n"
                )
            
            response_parts.extend([
                "",
                f"📚 RAG EMBEDDING STATUS:",
                f"✅ Successfully embedded: {len(embedded_urls)} URLs",
                f"❌ Failed to embed: {len(failed_urls)} URLs",
                ""
            ])
            
            if embedded_urls:
                response_parts.append("✅ SUCCESSFULLY EMBEDDED:")
                for item in embedded_urls:
                    response_parts.append(f"  • {item['title']}\n    {item['url']}")
                response_parts.append("")
            
            if failed_urls:
                response_parts.append("❌ FAILED TO EMBED:")
                for item in failed_urls:
                    response_parts.append(f"  • {item['title']}\n    {item['url']}\n    Error: {item['error']}")
                response_parts.append("")
            
            response_parts.extend([
                "💡 USAGE TIP:",
                "The embedded URLs are now available for RAG-based queries.",
                f"You can now ask questions about '{query}' and get answers based on the embedded content."
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            error_msg = f"❌ Error in SearchAndEmbeddingTool: {str(e)}"
            print(error_msg)
            return error_msg


# Create an instance of the tool for easy import
search_and_emb_tool = SearchAndEmbeddingTool()


# Test function
def test_search_and_embedding():
    """Test function for the SearchAndEmbeddingTool."""
    
    # Check if API key exists
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("❌ TAVILY_API_KEY not found in environment")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test the tool
    try:
        result = search_and_emb_tool._run(
            query="machine learning applications in healthcare"
        )
        print("\n" + "="*80)
        print("TOOL TEST RESULT:")
        print("="*80)
        print(result)
        print("="*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_search_and_embedding()
