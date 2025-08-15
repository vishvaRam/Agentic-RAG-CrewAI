import os
from dotenv import load_dotenv
load_dotenv()

from crewai_tools.tools import TavilySearchTool

def test_tavily():
    # Check API key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("❌ TAVILY_API_KEY not found in environment")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Create tool
    tool = TavilySearchTool(
        search_depth="basic",
        max_results=3,
        include_raw_content=False
    )
    
    # Test simple query
    try:
        result = tool.run("python programming")
        print(f"✅ Response type: {type(result)}")
        print(f"✅ Response: {result}")
        
        if isinstance(result, dict) and "results" in result:
            print(f"✅ Found {len(result['results'])} results")
        else:
            print("⚠️ Unexpected response format")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_tavily()
