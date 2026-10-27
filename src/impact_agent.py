
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
    temperature=float(temperature or 0),
    num_ctx=int(os.getenv("NUM_CTX", "16384")),
)


prompt = ChatPromptTemplate.from_template("""
You are a Senior Software Engineer acting as a Code Impact
and Testing Agent.

You are given a saved analysis of a software repository.
Use it as your primary source of information.

Repository code analysis:
{analysis}

User question:
{question}

Analyze the question and respond using these sections:

1. Understanding the Change
Explain what the user wants to change.

2. Directly Affected Files
List the files that are directly related to the feature.
For each file, explain its responsibility and why it matters.

3. Potentially Affected Files
Identify other files that may be affected through dependencies,
API calls, shared components, authentication, or data flow.
Explain the reason for each potential impact.

4. Possible Code Fixes
Explain what may need to change in each relevant file.
Do not invent exact code changes when the source code is unavailable.

5. Testing Plan
List the relevant tests to run or add.
Consider unit tests, API tests, integration tests, and regression
tests where applicable.
Do not claim a test exists unless the analysis confirms it.

6. Recommended Order
Suggest a sensible order for implementing and testing the changes.

7. Confidence and Unknowns
Separate confirmed facts from reasonable inferences.
Explicitly state when the analysis does not contain enough
information to confirm a dependency or recommend an exact fix.

Rules:
- Use file paths from the provided analysis.
- Never invent file names, routes, functions, or dependencies.
- Do not assume that a file is affected without explaining why.
- Distinguish directly affected files from files that might be affected.
- If source code must be inspected to confirm an impact, say so.
- Be concise, specific, and practical.
- Do not claim to have executed tests.
""")

chain = prompt | model


def ask_impact(analysis: str, question: str) -> str:
    response = chain.invoke({
        "analysis": analysis,
        "question": question
    })
    return response.content


def stream_impact(analysis: str, question: str):
    for chunk in chain.stream({
        "analysis": analysis,
        "question": question
    }):
        if chunk.content:
            yield chunk.content
