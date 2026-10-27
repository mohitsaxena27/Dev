import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def read_repository(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    print("Repository:", data["full_name"])
    print("Description:", data["description"])
    print("Default branch:", data["default_branch"])

    contents_url = f"{url}/contents"
    contents_response = requests.get(
        contents_url, headers=HEADERS, timeout=15
    )
    contents_response.raise_for_status()

    print("\nFiles and folders:")
    for item in contents_response.json():
        print(f"- {item['name']} ({item['type']})")


def read_file(owner: str, repo: str, path: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    data = response.json()
    content = base64.b64decode(data["content"]).decode("utf-8")

    print(f"\n--- {path} ---\n")
    print(content)


def get_file_content(owner: str, repo: str, path: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    response = requests.get(
        url, headers=HEADERS, timeout=15
    )
    response.raise_for_status()

    data = response.json()
    return base64.b64decode(data["content"]).decode("utf-8")


def list_source_files(owner: str, repo: str):
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    repo_response = requests.get(
        base_url, headers=HEADERS, timeout=15
    )
    repo_response.raise_for_status()

    branch = repo_response.json()["default_branch"]

    commit_response = requests.get(
        f"{base_url}/commits/{branch}",
        headers=HEADERS,
        timeout=15,
    )
    commit_response.raise_for_status()

    tree_sha = commit_response.json()["commit"]["tree"]["sha"]

    tree_response = requests.get(
        f"{base_url}/git/trees/{tree_sha}?recursive=1",
        headers=HEADERS,
        timeout=30,
    )
    tree_response.raise_for_status()

    files = [
        item["path"]
        for item in tree_response.json()["tree"]
        if item["type"] == "blob"
        and item["path"].endswith(
            (".py", ".js", ".jsx", ".ts", ".tsx")
        )
    ]

    return files


if __name__ == "__main__":
    if not GITHUB_OWNER or not GITHUB_REPO:
        raise ValueError(
            "Please set GITHUB_OWNER and GITHUB_REPO in your .env file."
        )

    read_repository(GITHUB_OWNER, GITHUB_REPO)
    read_file(GITHUB_OWNER, GITHUB_REPO, "README.md")

    print("\nSource files:")
    for file_path in list_source_files(GITHUB_OWNER, GITHUB_REPO):
        print(f"- {file_path}")