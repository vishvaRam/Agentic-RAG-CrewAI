import os
import json
import sys
from typing import Dict, Any

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except Exception:
    pass

# Ensure we can import tools from your package path if running from root
# Adjust sys.path as needed if your repo structure differs
if "tools" not in "".join(sys.path):
    sys.path.append(os.path.abspath("."))

try:
    from tools.youtube_tool import YouTubeSearchTool, YouTubeTranscriptTool
except Exception as e:
    print("Error: Could not import tools from tools.youtube_tool. Make sure your file and classes exist.")
    print(f"Import error: {e}")
    sys.exit(1)

def print_video_row(idx: int, v: Dict[str, Any]) -> None:
    print(f"{idx}. {v.get('title', '(no title)')} ({v.get('duration_formatted', '00:00')})")
    print(f"   URL: {v.get('video_url', '')}")
    print(f"   Channel: {v.get('channel_title', '')} | Views: {v.get('view_count', 0)}")
    print(f"   Published: {v.get('published_at', '')}")
    print(f"   Score: {v.get('relevance_score', 0):.2f}\n")

def main():
    # Check API key
    if not os.getenv("YOUTUBE_API_KEY"):
        print("Error: Please set YOUTUBE_API_KEY environment variable (e.g., in a .env file).")
        return

    # Settings
    TOPIC = "AI in healthcare"
    DAYS_BACK = 7
    MAX_RESULTS = 5
    MAX_TO_TRANSCRIBE = 3  # how many from the search to transcribe

    # Instantiate tools
    try:
        search_tool = YouTubeSearchTool()
    except Exception as e:
        print(f"Error initializing search tool: {e}")
        return

    transcript_tool = YouTubeTranscriptTool()

    # Search
    print(f"Searching YouTube for: {TOPIC}")
    try:
        results_json = search_tool._run(topic=TOPIC, max_results=MAX_RESULTS, days_back=DAYS_BACK)
        results = json.loads(results_json)
    except Exception as e:
        print(f"Error during search: {e}")
        return

    if results.get("error"):
        print(f"Search error: {results['error']}")
        return

    videos = results.get("videos", [])
    print(f"\nFound {results.get('total_found', 0)} videos for topic '{TOPIC}':\n")
    for i, video in enumerate(videos, start=1):
        print_video_row(i, video)

    if not videos:
        print("No videos to transcribe.")
        return

    # Transcribe
    to_process = videos[:MAX_TO_TRANSCRIBE]
    print(f"Transcribing up to {len(to_process)} video(s) and appending to output/transcriptions.txt ...\n")

    for idx, video in enumerate(to_process, start=1):
        vid = video.get("video_id")
        desc = video.get("description", "")
        try:
            # Updated call - removed max_summary_length parameter
            resp_json = transcript_tool._run(
                video_id=vid,
                video_description=desc,
                language_preference="en"
            )
            resp = json.loads(resp_json)
            
            # Updated status checking for simplified response
            status = resp.get("status", "unknown")
            source_type = resp.get("source_type", "")
            word_count = resp.get("word_count", 0)
            
            if status == "success":
                print(f"[{idx}/{len(to_process)}] {video.get('title', '(no title)')} -> ✓ {source_type} ({word_count} words)")
            elif status == "error":
                print(f"[{idx}/{len(to_process)}] {video.get('title', '(no title)')} -> ✗ error: {resp.get('error', 'unknown error')}")
            else:
                print(f"[{idx}/{len(to_process)}] {video.get('title', '(no title)')} -> {status}")
                
        except Exception as e:
            print(f"[{idx}/{len(to_process)}] {video.get('title', '(no title)')} -> exception: {e}")

    print(f"\nDone. Check output/transcriptions.txt for appended full transcripts.")
    
    # Optional: Show file info
    transcript_file = "output/transcriptions.txt"
    if os.path.exists(transcript_file):
        file_size = os.path.getsize(transcript_file)
        print(f"Transcript file size: {file_size:,} bytes")

if __name__ == "__main__":
    main()
