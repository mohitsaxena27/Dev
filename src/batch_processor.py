
from collections import defaultdict
from github_reader import get_file_content
from analyzer import analyze_file


def create_batches(files, batch_size=5):
    folders = defaultdict(list)

    for path in files:
        folder = path.rsplit("/", 1)[0] if "/" in path else "."
        folders[folder].append(path)

    batches = []

    for folder, paths in sorted(folders.items()):
        for start in range(0, len(paths), batch_size):
            batches.append({
                "folder": folder,
                "files": paths[start:start + batch_size]
            })

    return batches


def analyze_batches(owner, repo, batches):
    results = []

    for number, batch in enumerate(batches, start=1):
        print(
            f"\nBatch {number}/{len(batches)}: "
            f"{batch['folder']}"
        )

        batch_results = [
            f"## Folder: {batch['folder']}\n"
        ]

        for path in batch["files"]:
            print(f"  Analyzing: {path}")

            try:
                content = get_file_content(owner, repo, path)

                if not content.strip():
                    continue

                analysis = analyze_file(path, content)
                batch_results.append(
                    f"### {path}\n\n{analysis}\n"
                )

            except Exception as error:
                print(f"  Failed: {path}: {error}")

        results.append("\n".join(batch_results))

    return results