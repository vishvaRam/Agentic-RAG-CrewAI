from typing import Dict, Any
from crewai.flow.flow import Flow, listen, start
from crew.research_crew import ResearchCrew
from crew.blog_crew import BlogWritingCrew
from dotenv import load_dotenv

load_dotenv()

class BlogWritingFlow(Flow):
    """
    Flow for automated blog writing with separated research and content creation crews.
    """
    def __init__(self, topic: str = None, word_count: str = None, read_time: str = None):
        super().__init__()
        # Store inputs as instance variables
        self.topic = topic or "The impact of AI on education"
        self.word_count = word_count or "1200"
        self.read_time = read_time or "6"
        self.research_crew = ResearchCrew()
        self.blog_crew = BlogWritingCrew()

    @start()
    def initiate_blog_creation(self) -> Dict[str, Any]:
        """
        Initialize flow with stored user inputs.
        """
        inputs = {
            "topic": self.topic,
            "word_count": self.word_count,
            "read_time": self.read_time
        }
        print(f"🚀 Starting blog creation flow for: {inputs['topic']}")
        return inputs

    @listen(initiate_blog_creation)
    def research_phase(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 1: Research and populate RAG knowledge base
        """
        print(f"🔍 Phase 1: Research and Knowledge Gathering for '{inputs['topic']}'")
        # Execute research crew
        research_result = self.research_crew.crew().kickoff(inputs=inputs)
        print("✅ Research phase completed!")
        print(f"📊 Research summary: {research_result}")
        return {
            **inputs,
            "research_completed": True,
            "research_result": str(research_result)
        }

    @listen(research_phase)
    def content_creation_phase(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Create content, publish, and generate social media post.
        """
        print(f"✍️ Phase 2: Content Creation, Publishing & Social Media for '{inputs['topic']}'")
        # Execute blog writing crew
        blog_result = self.blog_crew.crew().kickoff(inputs=inputs)
        print("✅ Content creation phase completed!")
        return {
            **inputs,
            "content_completed": True,
            "blog_result": str(blog_result),
            "final_output": str(blog_result)
        }

# Create flow instance for import
blog_writing_flow = BlogWritingFlow()
