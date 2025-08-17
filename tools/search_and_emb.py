import os
import json
from typing import Type, Dict, List, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field, PrivateAttr
from crewai.tools import BaseTool
from crewai_tools.tools import TavilySearchTool
from tools.rag_tool import rag_tool
from tools.youtube_tool import YouTubeSearchTool, YouTubeTranscriptTool

# Load .env variables
load_dotenv()

class SearchAndEmbeddingInput(BaseModel):
    query: str = Field(..., description="The information need or research query")

class SearchAndEmbeddingTool(BaseTool):
    """1) Web search → RAG embed  2) YouTube search → full-text transcripts"""

    name: str = "Search & Embed (Web + YouTube)"
    description: str = (
        "Uses Tavily to find web pages and embeds them with RAG. "
        "Uses YouTube API to find related videos and saves full transcripts. "
        "Returns a structured JSON summary of everything done."
    )
    args_schema: Type[BaseModel] = SearchAndEmbeddingInput

    # Private attrs - correctly imported from pydantic
    _tavily: TavilySearchTool = PrivateAttr()
    _yt_search: YouTubeSearchTool = PrivateAttr()
    _yt_transcribe: YouTubeTranscriptTool = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        tavily_key = os.getenv("TAVILY_API_KEY")
        yt_key = os.getenv("YOUTUBE_API_KEY")
        if not tavily_key:
            raise ValueError("TAVILY_API_KEY missing")
        if not yt_key:
            raise ValueError("YOUTUBE_API_KEY missing")

        self._tavily = TavilySearchTool(
            api_key=tavily_key,
            search_depth="basic",
            max_results=5,
            include_raw_content=False,
        )
        self._yt_search = YouTubeSearchTool()
        self._yt_transcribe = YouTubeTranscriptTool()

    def _run(self, query: str) -> str:
        web_out = self._search_web_and_embed(query)
        yt_out = self._search_youtube_and_transcribe(query)

        summary = {
            "web_embedded": len(web_out["embedded"]),
            "web_failed": len(web_out["failed"]),
            "yt_found": len(yt_out["videos"]),
            "yt_transcribed": sum(1 for r in yt_out["transcripts"] if r["status"] == "success"),
        }

        return json.dumps(
            {"query": query, "web": web_out, "youtube": yt_out, "summary": summary},
            indent=2,
        )

    def _search_web_and_embed(self, query: str) -> Dict[str, Any]:
        try:
            raw = self._tavily.run(query)
            data = json.loads(raw) if isinstance(raw, str) else raw
            results: List[Dict[str, Any]] = data.get("results", [])
        except Exception as e:
            return {"error": str(e), "embedded": [], "failed": []}

        embedded, failed = [], []

        for item in results:
            url, title = item.get("url"), item.get("title", "Untitled")
            if not url:
                continue
            try:
                # Adding web urls to RAG
                rag_tool.add(url, data_type="web_page")
                embedded.append({"url": url, "title": title})
            except Exception as e:
                failed.append({"url": url, "title": title, "error": str(e)})

        return {"embedded": embedded, "failed": failed}

    def _search_youtube_and_transcribe(self, query: str) -> Dict[str, Any]:
        try:
            raw = self._yt_search._run(topic=query, max_results=5, days_back=90)
            data = json.loads(raw)
            videos: List[Dict[str, Any]] = data.get("videos", [])
            
        except Exception as e:
            print("*"*50)
            print(f"Error searching YouTube: {e}")
            return {"error": str(e), "videos": [], "transcripts": []}

        transcripts = []
        for v in videos:
            vid = v["video_id"]
            desc = v.get("description", "")
            try:
                t_raw = self._yt_transcribe._run(
                    video_id=vid, video_description=desc, language_preference="en", topic=query
                )
                t_data = json.loads(t_raw)
                transcripts.append(
                    {
                        "video_id": vid,
                        "status": t_data.get("status", "unknown"),
                        "source": t_data.get("source_type", "n/a"),
                        "word_count": t_data.get("word_count", 0),
                    }
                )
            except Exception as e:
                transcripts.append({"video_id": vid, "status": "error", "error": str(e)})
                
        transcript_file = f"output/transcriptions/transcript_{query}.txt"
        rag_tool.add(transcript_file, data_type="text")
        rag_added_status = True
        
        return {"videos": videos, "transcripts": transcripts,"rag_transcript_added": rag_added_status}

# Create tool instance
search_and_emb_tool = SearchAndEmbeddingTool()
