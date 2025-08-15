import os
import warnings
warnings.filterwarnings('ignore')
from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.project import CrewBase, agent, crew, task# noqa: E402
from tools.rag_tool import rag_tool# noqa: E402


@CrewBase
class BlogWritingCrew:
    """Blog Writing Crew with only Draft Creator and Senior Writer."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        self.rag_tool = rag_tool
        self.gemini_flash = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.2,
        )

    @agent
    def draft_creator(self) -> Agent:
        return Agent(
            config=self.agents_config["draft_creator"],  # type: ignore
            tools=[self.rag_tool],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
        )

    @agent
    def senior_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["senior_writer"],  # type: ignore
            tools=[self.rag_tool],
            llm=self.gemini_flash,
            verbose=True,
            allow_delegation=True,
            max_iter=6,
        )

    @task
    def draft_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config["draft_creation_task"],  # type: ignore
            agent=self.draft_creator(),
            output_file="output/draft_creation_task.md",
        )

    @task
    def final_writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_writing_task"],  # type: ignore
            agent=self.senior_writer(),
            context=[self.draft_creation_task()],
            output_file="output/final_writing_task.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # type: ignore
            tasks=self.tasks,  # type: ignore
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder={
                "provider": "google",
                "config": {
                    "model": "models/embedding-001",
                    "api_key": os.getenv("GEMINI_API_KEY")
                }
            },
            max_rpm=30,
            language="en",  # type: ignore
        )
