"""
Thin wrapper around PyGithub. Every method takes the repo / token / commit
as parameters - nothing about a specific repository is ever hardcoded here.
"""
from typing import List, Optional
import base64

from github import Github, GithubException, InputGitTreeElement

from config import get_settings

settings = get_settings()

DOC_EXTENSIONS = (".md", ".mdx", ".rst", ".txt")


def _client(token: Optional[str]) -> Github:
    resolved = token or settings.github_token
    if not resolved:
        raise ValueError(
            "No GitHub token available. Set GITHUB_TOKEN in the backend .env, "
            "or paste a token when connecting the repo."
        )
    return Github(resolved)


def get_repo_metadata(owner: str, name: str, token: Optional[str] = None) -> dict:
    gh = _client(token)
    repo = gh.get_repo(f"{owner}/{name}")
    return {
        "full_name": repo.full_name,
        "default_branch": repo.default_branch,
        "description": repo.description,
    }


def list_recent_commits(owner: str, name: str, token: Optional[str] = None, limit: int = 20) -> List[dict]:
    gh = _client(token)
    repo = gh.get_repo(f"{owner}/{name}")
    commits = []
    for c in repo.get_commits()[:limit]:
        commits.append({
            "sha": c.sha,
            "short_sha": c.sha[:7],
            "message": (c.commit.message or "").split("\n")[0],
            "author": c.commit.author.name if c.commit.author else None,
            "date": c.commit.author.date if c.commit.author else None,
            "files_changed": c.files.totalCount if hasattr(c.files, "totalCount") else len(list(c.files)),
        })
    return commits


def get_commit_diff(owner: str, name: str, sha: str, token: Optional[str] = None) -> dict:
    """Returns the full commit message plus a concatenated, per-file patch text."""
    gh = _client(token)
    repo = gh.get_repo(f"{owner}/{name}")
    commit = repo.get_commit(sha)

    file_diffs = []
    for f in commit.files:
        patch = f.patch or "(binary or too large to diff)"
        file_diffs.append(
            f"### {f.filename} (+{f.additions}/-{f.deletions}, {f.status})\n```diff\n{patch}\n```"
        )

    return {
        "message": commit.commit.message,
        "files": [f.filename for f in commit.files],
        "diff_text": "\n\n".join(file_diffs) if file_diffs else "(no file changes found)",
    }


def list_doc_files(owner: str, name: str, token: Optional[str] = None) -> List[str]:
    """Walks the repo tree and returns paths of documentation-like files."""
    gh = _client(token)
    repo = gh.get_repo(f"{owner}/{name}")
    tree = repo.get_git_tree(repo.default_branch, recursive=True)
    return [
        item.path for item in tree.tree
        if item.type == "blob" and item.path.lower().endswith(DOC_EXTENSIONS)
    ]


def get_file_content(owner: str, name: str, path: str, token: Optional[str] = None) -> str:
    gh = _client(token)
    repo = gh.get_repo(f"{owner}/{name}")
    content_file = repo.get_contents(path)
    return base64.b64decode(content_file.content).decode("utf-8", errors="ignore")


def create_pull_request(
    owner: str,
    name: str,
    branch_name: str,
    file_updates: List[dict],  # [{"path": ..., "new_content": ...}]
    pr_title: str,
    pr_body: str,
    token: Optional[str] = None,
) -> str:
    """Creates a branch, commits the doc updates, and opens a PR. Returns the PR URL."""
    gh = _client(token)
    repo = gh.get_repo(f"{owner}/{name}")
    base_branch = repo.default_branch
    base_ref = repo.get_git_ref(f"heads/{base_branch}")

    try:
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)
    except GithubException as e:
        if e.status != 422:  # 422 = ref already exists, safe to reuse
            raise

    for update in file_updates:
        try:
            existing = repo.get_contents(update["path"], ref=branch_name)
            repo.update_file(
                path=update["path"],
                message=f"docs: update {update['path']} (Doc-Drift Guardian)",
                content=update["new_content"],
                sha=existing.sha,
                branch=branch_name,
            )
        except GithubException:
            repo.create_file(
                path=update["path"],
                message=f"docs: add {update['path']} (Doc-Drift Guardian)",
                content=update["new_content"],
                branch=branch_name,
            )

    pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base=base_branch)
    return pr.html_url
