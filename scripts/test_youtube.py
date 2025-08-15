import os
import json
from tools.youtube_tool import YouTubeSearchTool

# NEW: load environment variables from .env
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())  # loads variables from the first .env found up the directory tree
except Exception:
    # If python-dotenv isn't installed, the script still runs but will rely on real env vars.
    pass

def main():
    # Make sure YOUTUBE_API_KEY is set in environment (from OS env or .env)
    if not os.getenv("YOUTUBE_API_KEY"):
        print("Error: Please set YOUTUBE_API_KEY environment variable (e.g., in a .env file).")
        return

    # Create the tool instance
    yt_tool = YouTubeSearchTool()

    # Search topic
    topic = "AI in healthcare"
    print(f"Searching YouTube for: {topic}")

    try:
        results_json = yt_tool._run(topic=topic, max_results=5, days_back=7)
        results = json.loads(results_json)

        if results.get("error"):
            print(f"Error: {results['error']}")
            return

        print(f"\nFound {results.get('total_found', 0)} videos for topic '{topic}':\n")

        for i, video in enumerate(results.get("videos", []), start=1):
            print(f"{i}. {video['title']} ({video['duration_formatted']})")
            print(f"   URL: {video['video_url']}")
            print(f"   Channel: {video['channel_title']} | Views: {video['view_count']}")
            print(f"   Published: {video['published_at']}")
            print(f"   Score: {video['relevance_score']:.2f}\n")

    except Exception as e:
        print(f"Error running YouTube search: {e}")

if __name__ == "__main__":
    main()
