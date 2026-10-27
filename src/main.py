import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from github_reader import HEADERS, get_file_content, list_source_files
from batch_processor import analyze_batches, create_batches
from impact_agent import ask_impact, stream_impact
from targeted_agent import run_targeted, stream_targeted
from readme_generator import generate_readme, stream_readme

load_dotenv()

OLLAMA_URL = os.getenv("BASE_URL", "")
HOST = os.getenv("HOST", "127.0.0.1")  # localhost only
PORT = int(os.getenv("PORT", "8000"))

ANALYSIS_DIR = Path("analysis")
ANALYSIS_DIR.mkdir(exist_ok=True)
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
# Your existing summary file. Used whenever a request has no owner/repo.
DEFAULT_ANALYSIS = Path(os.getenv("ANALYSIS_FILE", "code_analysis.md"))

NAME_PATTERN = r"^[A-Za-z0-9_.-]+$"

app = FastAPI(
    title="AI SDLC - Code Impact Agent",
    description="Analyze GitHub repos, generate READMEs, and run impact analysis.",
    version="1.0.0",
)

# In-memory job store (resets when the server restarts)
JOBS: dict[str, dict] = {}


# ---------- Request models ----------
class AnalyzeRequest(BaseModel):
    owner: str = Field(..., pattern=NAME_PATTERN, examples=["mohitsaxena27"])
    repo: str = Field(..., pattern=NAME_PATTERN, examples=["ai_sdlc"])
    batch_size: int = Field(5, ge=1, le=20)


class ImpactRequest(BaseModel):
    question: str = Field(..., min_length=3)
    use_code: bool = True  # False = answer from the summary only
    owner: Optional[str] = Field(None, pattern=NAME_PATTERN)
    repo: Optional[str] = Field(None, pattern=NAME_PATTERN)


class ReadmeRequest(BaseModel):
    owner: Optional[str] = Field(None, pattern=NAME_PATTERN)
    repo: Optional[str] = Field(None, pattern=NAME_PATTERN)


# ---------- Helpers ----------
def analysis_path(owner: Optional[str], repo: Optional[str]) -> Path:
    if owner and repo:
        return ANALYSIS_DIR / f"{owner}__{repo}.md"
    if owner or repo:
        raise HTTPException(400, "Provide both owner and repo, or neither.")
    return DEFAULT_ANALYSIS


def load_analysis(owner: Optional[str], repo: Optional[str]) -> str:
    path = analysis_path(owner, repo)
    if not path.exists():
        raise HTTPException(
            404,
            f"No analysis found at '{path}'. Run POST /analysis first.",
        )
    return path.read_text(encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_repo(req) -> tuple[str, str]:
    owner = req.owner or GITHUB_OWNER
    repo = req.repo or GITHUB_REPO
    if not owner or not repo:
        raise HTTPException(500, "Set GITHUB_OWNER and GITHUB_REPO in .env")
    return owner, repo


def run_analysis_job(job_id: str, owner: str, repo: str, batch_size: int):
    job = JOBS[job_id]
    try:
        job["status"] = "running"
        files = list_source_files(owner, repo)
        if not files:
            raise ValueError("No source files (.py/.js/.jsx/.ts/.tsx) found.")

        batches = create_batches(files, batch_size)
        job["total_files"] = len(files)
        job["total_batches"] = len(batches)

        results = []
        for number, batch in enumerate(batches, start=1):
            # One batch at a time so we can report progress
            results.extend(analyze_batches(owner, repo, [batch]))
            job["completed_batches"] = number

        analysis = f"# Repository: {owner}/{repo}\n\n" + "\n\n".join(results)
        path = analysis_path(owner, repo)
        path.write_text(analysis, encoding="utf-8")

        job["status"] = "completed"
        job["analysis_file"] = str(path)
    except Exception as error:
        job["status"] = "failed"
        job["error"] = str(error)
    finally:
        job["finished_at"] = now()


# ---------- Endpoints ----------
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/health", tags=["System"])
def health():
    """Checks the API, Ollama server, and GitHub token."""
    ollama = {"url": OLLAMA_URL, "reachable": False}
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        ollama["reachable"] = r.ok
        if r.ok:
            ollama["models"] = [m["name"] for m in r.json().get("models", [])]
    except Exception as error:
        ollama["error"] = str(error)

    ollama["configured_model"] = os.getenv("LLM_MODEL")
    return {
        "status": "ok",
        "time": now(),
        "ollama": ollama,
        "github_token_set": bool(os.getenv("GITHUB_TOKEN")),
        "project": {
            "owner": GITHUB_OWNER,
            "repo": GITHUB_REPO,
            "analysis_file": str(DEFAULT_ANALYSIS),
            "analysis_exists": DEFAULT_ANALYSIS.exists(),
        },
        "saved_analyses": sorted(p.name for p in ANALYSIS_DIR.glob("*.md")),
    }


@app.get("/repos/{owner}/{repo}", tags=["GitHub"])
def repo_info(owner: str, repo: str):
    """Basic repo details and top-level contents."""
    base = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        info = requests.get(base, headers=HEADERS, timeout=15)
        info.raise_for_status()
        contents = requests.get(f"{base}/contents", headers=HEADERS, timeout=15)
        contents.raise_for_status()
    except requests.HTTPError as error:
        raise HTTPException(error.response.status_code, str(error))
    data = info.json()
    return {
        "full_name": data["full_name"],
        "description": data["description"],
        "default_branch": data["default_branch"],
        "top_level": [
            {"name": i["name"], "type": i["type"]} for i in contents.json()
        ],
    }


@app.get("/repos/{owner}/{repo}/files", tags=["GitHub"])
def repo_files(owner: str, repo: str):
    """Lists all source files (.py, .js, .jsx, .ts, .tsx)."""
    try:
        files = list_source_files(owner, repo)
    except requests.HTTPError as error:
        raise HTTPException(error.response.status_code, str(error))
    return {"count": len(files), "files": files}


@app.get("/repos/{owner}/{repo}/file", tags=["GitHub"])
def repo_file(owner: str, repo: str, path: str):
    """Returns the content of one file. Example: ?path=src/app.py"""
    try:
        content = get_file_content(owner, repo, path)
    except requests.HTTPError as error:
        raise HTTPException(error.response.status_code, str(error))
    return {"path": path, "content": content}


@app.post("/analysis", status_code=202, tags=["Analysis"])
def start_analysis(req: AnalyzeRequest, background: BackgroundTasks):
    """Starts repo analysis in the background. Poll GET /jobs/{job_id}."""
    for job in JOBS.values():
        if (
            job["owner"] == req.owner
            and job["repo"] == req.repo
            and job["status"] in ("queued", "running")
        ):
            raise HTTPException(409, f"Analysis already running: {job['job_id']}")

    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "job_id": job_id,
        "owner": req.owner,
        "repo": req.repo,
        "status": "queued",
        "total_files": 0,
        "total_batches": 0,
        "completed_batches": 0,
        "error": None,
        "started_at": now(),
        "finished_at": None,
    }
    background.add_task(
        run_analysis_job, job_id, req.owner, req.repo, req.batch_size
    )
    return JOBS[job_id]


@app.get("/jobs", tags=["Analysis"])
def list_jobs():
    return list(JOBS.values())


@app.get("/jobs/{job_id}", tags=["Analysis"])
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    return job


@app.get("/analysis/{owner}/{repo}", tags=["Analysis"])
def get_analysis(owner: str, repo: str):
    """Returns the saved analysis markdown for a repo."""
    return {"owner": owner, "repo": repo, "analysis": load_analysis(owner, repo)}


@app.post("/impact", tags=["Impact"])
def impact(req: ImpactRequest):
    """Impact + testing analysis for a question. Owner/repo optional."""
    analysis = load_analysis(req.owner, req.repo)
    try:
        if req.use_code:
            owner, repo = project_repo(req)
            answer, files, usage = run_targeted(analysis, req.question, owner, repo)
            return {"question": req.question, "answer": answer,
                    "files_read": files, "usage": usage}
        answer = ask_impact(analysis=analysis, question=req.question)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(502, f"LLM error: {error}")
    return {"question": req.question, "answer": answer}


@app.post("/readme", tags=["README"])
def readme(req: ReadmeRequest):
    """Generates a README.md from the saved analysis."""
    analysis = load_analysis(req.owner, req.repo)
    try:
        content = generate_readme(analysis)
    except Exception as error:
        raise HTTPException(502, f"LLM error: {error}")

    if req.owner and req.repo:
        out = ANALYSIS_DIR / f"{req.owner}__{req.repo}_README.md"
        out.write_text(content, encoding="utf-8")
    return {"readme": content}


# ---------- Streaming (Server-Sent Events) ----------
def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def sse_stream(token_generator, on_complete=None):
    """Wraps a token generator as SSE: status -> token* -> done (or error)."""
    full_text = []
    try:
        yield sse_event("status", {"message": "Thinking..."})
        for token in token_generator:
            if isinstance(token, dict):  # status / files events
                yield sse_event(token["event"], token["data"])
                continue
            full_text.append(token)
            yield sse_event("token", {"token": token})
        if on_complete:
            on_complete("".join(full_text))
        yield sse_event("done", {"message": "Finished"})
    except Exception as error:
        yield sse_event("error", {"error": str(error)})


def sse_response(generator) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # stops nginx from buffering
        },
    )


@app.post("/impact/stream", tags=["Impact"])
def impact_stream(req: ImpactRequest):
    """Same as /impact but streams the answer token by token."""
    analysis = load_analysis(req.owner, req.repo)
    if req.use_code:
        owner, repo = project_repo(req)
        tokens = stream_targeted(analysis, req.question, owner, repo)
    else:
        tokens = stream_impact(analysis=analysis, question=req.question)
    return sse_response(sse_stream(tokens))


@app.post("/readme/stream", tags=["README"])
def readme_stream(req: ReadmeRequest):
    """Same as /readme but streams the README as it is written."""
    analysis = load_analysis(req.owner, req.repo)

    def save(text: str):
        if req.owner and req.repo:
            out = ANALYSIS_DIR / f"{req.owner}__{req.repo}_README.md"
            out.write_text(text, encoding="utf-8")

    return sse_response(sse_stream(stream_readme(analysis), on_complete=save))


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)