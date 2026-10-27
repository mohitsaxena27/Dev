"""
Code-aware agent.

1. Use the saved summary (your .md file) as a map of the repo.
2. Pick only the files relevant to the question.
3. Read those files from GitHub (real source code).
4. Answer from the actual code, with file paths and line numbers.
"""
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.prompts import ChatPromptTemplate

from github_reader import get_file_content, list_source_files
from impact_agent import model

MAX_FILES = int(os.getenv("MAX_FILES", "4"))
MAX_FILE_CHARS = int(os.getenv("MAX_FILE_CHARS", "9000"))
CANDIDATES = 30
FILE_LIST_TTL = 600  # seconds
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))

_cache = {"key": None, "time": 0.0, "files": []}

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "in", "on", "of", "for", "to", "and",
    "or", "which", "what", "where", "how", "used", "use", "does", "do", "i",
    "me", "my", "we", "it", "this", "that", "with", "from", "tell", "give",
    "want", "need", "should", "can", "will", "be", "by", "at", "as", "all",
}
API_WORDS = ["api", "fetch", "url", "webhook", "route", "axios", "request"]
SYNONYMS = {
    "endpoint": API_WORDS, "endpoints": API_WORDS, "api": API_WORDS,
    "doc": ["documentation", "generate"], "docs": ["documentation", "generate"],
    "documentation": ["doc", "generate"],
    "login": ["auth", "token", "session"],
}


# ---------- Helpers ----------
def get_repo_files(owner: str, repo: str) -> list[str]:
    key = f"{owner}/{repo}"
    if _cache["key"] == key and time.time() - _cache["time"] < FILE_LIST_TTL:
        return _cache["files"]
    files = list_source_files(owner, repo)
    _cache.update(key=key, time=time.time(), files=files)
    return files


def tokens(text: str) -> set[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {w[:6] for w in words if w not in STOPWORDS and len(w) > 1}


def expand_question(question: str) -> set[str]:
    words = re.findall(r"[A-Za-z0-9]+", question.lower())
    extra = [s for w in words for s in SYNONYMS.get(w, [])]
    return tokens(question) | tokens(" ".join(extra))


def split_sections(analysis: str) -> dict[str, str]:
    """Maps file path -> its section in the summary (headers like '### path/to/file.js')."""
    parts = re.split(r"(?m)^#{2,4}\s+`?([\w./@\-\[\]]+\.\w+)`?\s*$", analysis)
    return {h.strip(): body for h, body in zip(parts[1::2], parts[2::2])}


def short(text: str, limit: int = 160) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def rank_files(question: str, files: list[str], sections: dict[str, str]) -> list[str]:
    q = expand_question(question)
    scored = []
    for path in files:
        folder, _, name = path.rpartition("/")
        score = (
            5 * len(q & tokens(name))
            + 2 * len(q & tokens(folder))
            + len(q & tokens(sections.get(path, "")))
        )
        scored.append((score, path))
    scored.sort(key=lambda item: (-item[0], item[1]))
    ranked = [p for s, p in scored if s > 0][:CANDIDATES]
    return ranked or files[:CANDIDATES]


# ---------- Token counting ----------
def get_usage(message) -> tuple[int, int]:
    """(input_tokens, output_tokens) reported by Ollama, or (0, 0) if absent."""
    meta = getattr(message, "usage_metadata", None) or {}
    if meta:
        return meta.get("input_tokens", 0), meta.get("output_tokens", 0)
    info = getattr(message, "response_metadata", None) or {}
    return info.get("prompt_eval_count", 0), info.get("eval_count", 0)


def new_usage() -> dict:
    return {"input": 0, "output": 0, "calls": 0, "peak_input": 0, "estimated": False}


def add_usage(usage: dict, message, fallback_in: int = 0, fallback_out: int = 0):
    """Adds one model call. Uses real counts; falls back to a ~4 chars/token estimate."""
    tokens_in, tokens_out = get_usage(message)
    if not (tokens_in or tokens_out):
        tokens_in, tokens_out = fallback_in, fallback_out
        usage["estimated"] = True
    usage["input"] += tokens_in
    usage["output"] += tokens_out
    usage["calls"] += 1
    usage["peak_input"] = max(usage["peak_input"], tokens_in)


SELECT_PROMPT = ChatPromptTemplate.from_template("""
You choose which source files must be read to answer a question about a codebase.

Question: {question}

Candidate files (path: short summary):
{candidates}

Return the paths of the files to read, at most {max_files}, most relevant first.
Copy each path exactly from the list above. Output one path per line and nothing else.
""")


def select_files(question: str, candidates: list[str],
                 sections: dict[str, str], valid: set[str], usage: dict) -> list[str]:
    lines = "\n".join(f"- {p}: {short(sections.get(p, ''))}" for p in candidates)
    message = (SELECT_PROMPT | model).invoke({
        "question": question, "candidates": lines, "max_files": MAX_FILES,
    })
    raw = re.sub(r"<think>.*?</think>", "", message.content, flags=re.S)
    add_usage(usage, message, (len(lines) + len(question)) // 4 + 80, len(raw) // 4)

    chosen = []
    for path in re.findall(r"[\w./@\-\[\]]+\.\w+", raw):
        if path in valid and path not in chosen:
            chosen.append(path)

    # Small models sometimes return too little: top up from the keyword ranking
    for path in candidates:
        if len(chosen) >= min(2, MAX_FILES):
            break
        if path not in chosen:
            chosen.append(path)
    return chosen[:MAX_FILES]


def read_files(owner: str, repo: str, paths: list[str]):
    def fetch(path):
        try:
            return path, get_file_content(owner, repo, path), None
        except Exception as error:
            return path, None, str(error)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(fetch, paths))


def numbered(text: str) -> str:
    lines, used = [], 0
    all_lines = text.splitlines()
    for number, line in enumerate(all_lines, start=1):
        used += len(line) + 1
        if used > MAX_FILE_CHARS:
            lines.append(f"[truncated: {len(all_lines) - number + 1} more lines not shown]")
            break
        lines.append(f"{number:>4}| {line}")
    return "\n".join(lines)


ANSWER_PROMPT = ChatPromptTemplate.from_template("""
You are a Senior Software Engineer helping a developer with an existing repository.

You have a saved summary of the relevant files and the ACTUAL SOURCE CODE of the
files chosen as most relevant. Lines are numbered as "number| code".

Summary of the relevant files:
{summary}

Source code:
{code}

Files that could not be read: {failed}
Other possibly relevant files that were NOT read: {unread}

Question: {question}

Respond in Markdown with these sections:

## Answer
Answer the question directly using exact values from the source code (URLs,
routes, function names, payload fields). Cite each as `path:line`.

## Evidence
Short code snippets that prove the answer, each with its file path and line numbers.

## What to update
Concrete changes, per file, for what the question implies. Show the exact code
change where useful. If the question is only informational, say which lines
you would touch if the value needed to change.

## Testing
What to verify after a change.

## Unknowns
Anything the code you were given does not show, such as values defined in other
files or environment variables. Name the files that should be opened next.

Rules:
- The source code is the source of truth. If the summary disagrees, trust the code.
- Never invent URLs, routes, functions or file names.
- If the code uses a variable or environment value for a URL, report the variable
  and where it is imported or defined, if visible.
- Be concise and specific.
""")


# ---------- Main entry points ----------
def stream_targeted(analysis: str, question: str, owner: str, repo: str):
    """Yields event dicts (status, files, usage) first, then answer text tokens."""
    yield {"event": "status", "data": {"message": "Finding the relevant files…"}}
    files = get_repo_files(owner, repo)
    valid = set(files)
    sections = {p: b for p, b in split_sections(analysis).items() if p in valid}

    candidates = rank_files(question, files, sections)
    usage = new_usage()
    selected = select_files(question, candidates, sections, valid, usage)
    yield {"event": "files", "data": {"files": selected}}

    yield {"event": "status", "data": {"message": f"Reading {len(selected)} files from GitHub…"}}
    results = read_files(owner, repo, selected)
    code = "\n\n".join(
        f"=== {path} ===\n{numbered(content)}"
        for path, content, error in results if content
    ) or "(no source files could be read)"
    failed = ", ".join(f"{p} ({e})" for p, c, e in results if e) or "none"
    unread = ", ".join([p for p in candidates if p not in selected][:8]) or "none"

    summary = "\n\n".join(
        f"### {p}\n{sections[p].strip()}" for p in selected if p in sections
    ) or analysis[:4000]

    yield {"event": "status", "data": {"message": "Analyzing the code…"}}
    last, out_chars = None, 0
    for chunk in (ANSWER_PROMPT | model).stream({
        "summary": summary, "code": code, "failed": failed,
        "unread": unread, "question": question,
    }):
        if chunk.content:
            out_chars += len(chunk.content)
            yield chunk.content
        if get_usage(chunk) != (0, 0):
            last = chunk  # only the final chunk carries the counts
    add_usage(usage, last, (len(summary) + len(code) + len(question)) // 4 + 250,
              out_chars // 4)
    yield {"event": "usage", "data": {
        **usage, "total": usage["input"] + usage["output"], "num_ctx": NUM_CTX,
    }}


def run_targeted(analysis: str, question: str, owner: str, repo: str):
    """Non-streaming version. Returns (answer, files_read, usage)."""
    text, files, usage = [], [], {}
    for item in stream_targeted(analysis, question, owner, repo):
        if isinstance(item, dict):
            if item["event"] == "files":
                files = item["data"]["files"]
            elif item["event"] == "usage":
                usage = item["data"]
        else:
            text.append(item)
    return "".join(text), files, usage