import warnings
warnings.filterwarnings('ignore')
from rich import print # noqa: E402
from flow.blog_flow import BlogWritingFlow # noqa: E402


def main():
    """Main function using CrewAI Flow with input parameters and usage tracking"""
    
    # Get user inputs
    print("\n[bold yellow]🚀 Blog Creation Setup[/bold yellow]")
    topic = input("Enter blog topic: ") or "The impact of AI on education"
    word_count = input("Enter approximate word count: ") or "1200"
    read_time = input("Enter approximate read time in minutes: ") or "6"
    
    print("\n[bold yellow]Starting Automated Blog Creation Flow[/bold yellow]")
    print(f"[bold cyan]Topic: {topic}[/bold cyan]")
    print(f"[bold cyan]Target: {word_count} words, {read_time} min read[/bold cyan]\n")
    
    # Create flow with inputs passed to constructor
    try:
        flow = BlogWritingFlow(topic=topic, word_count=word_count, read_time=read_time)
        result = flow.kickoff()
        
        print("\n" + "=" * 60)
        print("[bold green]🎉 BLOG CREATION FLOW COMPLETED![/bold green]")
        print("=" * 60)
        print("[bold white]Final Result:[/bold white]")
        print(result.get('final_output', 'No output generated'))
        print("=" * 60)
        
        # Display token usage metrics
        print("\n[bold blue]📊 USAGE METRICS[/bold blue]")
        print("=" * 40)
        
        # Get usage metrics from research crew
        research_crew = flow.research_crew.crew()
        if hasattr(research_crew, 'usage_metrics'):
            research_metrics = research_crew.usage_metrics
            print("[bold cyan]Research Phase:[/bold cyan]")
            print(f"  Total Tokens: {research_metrics.total_tokens:,}")
            print(f"  Prompt Tokens: {research_metrics.prompt_tokens:,}")
            print(f"  Completion Tokens: {research_metrics.completion_tokens:,}")
            print(f"  Successful Requests: {research_metrics.successful_requests}")
            if hasattr(research_metrics, 'cached_prompt_tokens'):
                print(f"  Cached Prompt Tokens: {research_metrics.cached_prompt_tokens:,}")
            print()
        
        # Get usage metrics from blog writing crew
        blog_crew = flow.blog_crew.crew()
        if hasattr(blog_crew, 'usage_metrics'):
            blog_metrics = blog_crew.usage_metrics
            print("[bold cyan]Content Creation Phase:[/bold cyan]")
            print(f"  Total Tokens: {blog_metrics.total_tokens:,}")
            print(f"  Prompt Tokens: {blog_metrics.prompt_tokens:,}")
            print(f"  Completion Tokens: {blog_metrics.completion_tokens:,}")
            print(f"  Successful Requests: {blog_metrics.successful_requests}")
            if hasattr(blog_metrics, 'cached_prompt_tokens'):
                print(f"  Cached Prompt Tokens: {blog_metrics.cached_prompt_tokens:,}")
            print()
        
        # Calculate and display total metrics
        total_tokens = (research_metrics.total_tokens if 'research_metrics' in locals() else 0) + \
                      (blog_metrics.total_tokens if 'blog_metrics' in locals() else 0)
        total_requests = (research_metrics.successful_requests if 'research_metrics' in locals() else 0) + \
                        (blog_metrics.successful_requests if 'blog_metrics' in locals() else 0)
        
        print("[bold green]Overall Total:[/bold green]")
        print(f"  Combined Total Tokens: {total_tokens:,}")
        print(f"  Combined LLM Requests: {total_requests}")
        print("=" * 40)
        
    except Exception as e:
        print(f"\n[bold red]❌ Error in blog creation flow: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main()
