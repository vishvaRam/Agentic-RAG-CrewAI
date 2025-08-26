# AI-Powered Blog Writing Assistant

An automated blog writing system that leverages CrewAI to create high-quality, well-researched blog posts. The project implements a multi-agent workflow for researching topics, generating content, and publishing blog posts with minimal human intervention.

## Core Components

### 1. Research Crew
- **Research Specialist**: Gathers and processes information on the given topic
- **Knowledge Base**: Populates a Retrieval-Augmented Generation (RAG) system with relevant data

### 2. Writing Crew
- **Draft Creator**: Generates initial blog post drafts
- **Senior Writer**: Refines content, ensures quality, and adds relevant images

### 3. Tools & Integrations
- **RAG System**: For fact-based content generation
- **Pexels API**: For sourcing relevant cover images
- **Dev.to Integration**: Optional publishing capability
- **Token Tracking**: Monitors API usage and costs

## Project Structure

- **`/crew`**: Contains agent implementations and configurations
  - `config/`: YAML files defining agent behaviors and tasks
  - `blog_crew.py`: Manages the blog writing agents
  - `research_crew.py`: Handles research-related agents

- **`/flow`**: Defines the workflow
  - `blog_flow.py`: Main workflow orchestration

- **`/output`**: Generated content storage
  - `blogs/`: Final blog posts
  - `drafts/`: Initial versions
  - `research/`: Collected research data
  - `publication/`: Publishing metadata

- **`/tools`**: Custom tools and integrations
  - `rag_tool.py`: Retrieval-Augmented Generation
  - `image_search_tool.py`: Image sourcing
  - `devto_publisher_tool.py`: Publishing interface

## Workflow

1. **Topic Research**: System gathers and processes information
2. **Draft Creation**: Initial content generation
3. **Content Refinement**: Polishing and enhancement
4. **Publishing**: Optional deployment to platforms
