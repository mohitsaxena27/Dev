#
# from langchain_ollama import ChatOllama
# from langchain_core.prompts import ChatPromptTemplate
#
# model = ChatOllama(
#     model="nemotron-3-nano:4b",
#     base_url="http://10.154.2.98:11434",
#     temperature=0
# )
#
# prompt = ChatPromptTemplate.from_template("""
# You are a technical documentation writer.
#
# Using the code analysis below, create a clear README.md
# for developers who are new to this project.
#
# Include:
# 1. Project overview
# 2. Main components
# 3. Important files and their responsibilities
# 4. Technologies identified in the analysis
#
# Only include information supported by the analysis.
# If information is unknown, clearly mark it as "Not identified".
#
# Code analysis:
# {analysis}
# """)
#
# chain = prompt | model
#
#
# def generate_readme(analysis: str) -> str:
#     response = chain.invoke({"analysis": analysis})
#     return response.content



from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv


load_dotenv()

llm_model = os.getenv("LLM_MODEL")
base_url = os.getenv("BASE_URL")
temperature = os.getenv("TEMPERATURE")

model = ChatOllama(
    model=llm_model,
    base_url=base_url,
    temperature=temperature
)


prompt = ChatPromptTemplate.from_template("""
You are a senior software engineer writing developer documentation.

Create a comprehensive README.md for the repository using
the code analysis provided below.

Include these sections:
1. Project Overview
2. Architecture (frontend, backend, and integrations)
3. Repository Structure
4. Important Folders and Files
5. Key Features
6. Technologies and Dependencies
7. Setup and Run Instructions
8. Environment Variables
9. Important API Routes, if identified

Rules:
- Use only facts supported by the analysis.
- Do not invent commands, routes, dependencies, or environment variables.
- Mark unknown information as "Not identified in the analysis".
- Avoid repeating the same information in multiple sections.
- Use Markdown headings, lists, and tables where appropriate.
- Output only the README content.

Code analysis:
{analysis}
""")

chain = prompt | model


def generate_readme(analysis: str) -> str:
    response = chain.invoke({"analysis": analysis})
    return response.content

def stream_readme(analysis: str):
    for chunk in chain.stream({"analysis": analysis}):
        if chunk.content:
            yield chunk.content