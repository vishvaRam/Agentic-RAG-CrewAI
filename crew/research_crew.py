import os
import warnings
warnings.filterwarnings('ignore')
from crewai import LLM, Agent, Crew, Process, Task # noqa: E402
from crewai.project import CrewBase, agent, crew, task # noqa: E402
from tools.search_and_emb import search_and_emb_tool# noqa: E402
from dotenv import load_dotenv # noqa: E402

load_dotenv()

@CrewBase
class ResearchCrew:
    """Research Crew for knowledge gathering and RAG population."""

    agents_config = "config/research_agents.yaml"
    tasks_config = "config/research_tasks.yaml"

    def __init__(self):
        self.search_and_emb_tool = search_and_emb_tool
        self.gemini_flash = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.01,
        )

    @agent
    def research_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["research_specialist"],
            tools=[self.search_and_emb_tool],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=1,
        )

    @task
    def research_and_embed_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_and_embed_task"],
            agent=self.research_specialist(),
            output_file="output/research/research_report_{topic}.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            max_rpm=10,
            language="en",
        )
