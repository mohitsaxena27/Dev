import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL")
BASE_URL = os.getenv("BASE_URL")

if not LLM_MODEL or not BASE_URL:
    raise ValueError(
        "Please set LLM_MODEL and BASE_URL in your .env file."
    )

model = ChatOllama(
    model=LLM_MODEL,
    base_url=BASE_URL,
    temperature=0,
)

prompt = ChatPromptTemplate.from_template("""
You are a software project analyst.

Analyze the following repository file.

File path: {file_path}

File content:
{file_content}

Explain briefly:

1. What this file does
2. Its important components
3. How it may relate to the overall project

Only use information supported by the provided content.
""")

chain = prompt | model


def analyze_file(file_path: str, file_content: str) -> str:
    response = chain.invoke({
        "file_path": file_path,
        "file_content": file_content,
    })

    return response.content
