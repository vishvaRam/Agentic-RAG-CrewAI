import os
# Warning control
import warnings
warnings.filterwarnings('ignore')
from rich import print  # noqa: E402
from crew.crew import BlogWritingCrew  # noqa: E402
from tools.search_and_emb import search_and_emb_tool  # noqa: E402


def manual_research(topic: str):
    """Run Search and Embedding Tool ONCE to populate RAG."""
    print(f"[bold green]🚀 Running one-time search & embedding for {topic}[/bold green]")
    query = f"{topic}"
    result = search_and_emb_tool.run(query)
    print(result)
    print("\n[bold green]✅ Knowledge base ready![/bold green]\n")


def main():
    topic = input("Enter blog topic: ") or "The impact of AI on education"
    word_count = input("Enter approximate word count: ") or "1200"
    read_time = input("Enter approximate read time in minutes: ") or "6"

    # Step 1: Populate RAG manually
    manual_research(topic)

    # Step 2: Kick off the Crew (Draft Creator -> Senior Writer)
    print(f"\n[bold yellow]Generating blog about: {topic}[/bold yellow]\n")
    crew = BlogWritingCrew()
    inputs = {"topic": topic, "word_count": word_count, "read_time": read_time}
    result = crew.crew().kickoff(inputs=inputs)

    print("\n" + "=" * 50)
    print("GENERATED BLOG POST:")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    main()
