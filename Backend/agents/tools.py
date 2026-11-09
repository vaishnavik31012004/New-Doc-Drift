"""
Function tools the ADK agents can call. Each tool is a plain, typed Python
function - ADK's FunctionTool introspects the signature/docstring to expose
it to the model, so nothing about a specific repo/commit is baked in here;
it all arrives as arguments at call time.
"""
from services import github_service, vector_store


def search_repo_docs(full_name: str, query: str) -> str:
    """Semantically searches the connected repository's indexed documentation
    for passages relevant to `query`.

    Args:
        full_name: The repository's "owner/name" identifier.
        query: A natural-language description of the code change to check docs against.

    Returns:
        The most relevant documentation passages, each prefixed with its file path.
    """
    hits = vector_store.search_docs(full_name, query, top_k=5)
    if not hits:
        return "No indexed documentation found for this repository."
    return "\n\n".join(f"[{h['path']}]\n{h['text']}" for h in hits)


def list_documentation_files(owner: str, name: str, token: str = "") -> str:
    """Lists every documentation-like file (.md, .mdx, .rst, .txt) in the repo.

    Args:
        owner: GitHub repository owner/org.
        name: GitHub repository name.
        token: Optional GitHub token override.
    """
    paths = github_service.list_doc_files(owner, name, token or None)
    return "\n".join(paths) if paths else "(no documentation files found)"


def read_documentation_file(owner: str, name: str, path: str, token: str = "") -> str:
    """Reads the full raw content of a single documentation file from the repo.

    Args:
        owner: GitHub repository owner/org.
        name: GitHub repository name.
        path: Path of the file within the repo, e.g. "README.md".
        token: Optional GitHub token override.
    """
    return github_service.get_file_content(owner, name, path, token or None)
