"""
The agents are instructed to respond in a simple, consistent block format
(see the prompts in pipeline.py). These functions parse that text into
structured data - no data is invented here, only what the model actually
produced is extracted.
"""
import re
from typing import List, Dict


def parse_drift_findings(text: str) -> List[Dict]:
    if not text or "NO_DRIFT_DETECTED" in text:
        return []

    blocks = re.split(r"\n(?=FILE:)", text.strip())
    findings = []
    for block in blocks:
        file_match = re.search(r"FILE:\s*(.+)", block)
        sev_match = re.search(r"SEVERITY:\s*(low|medium|high)", block, re.IGNORECASE)
        issue_match = re.search(r"ISSUE:\s*(.+)", block, re.DOTALL)
        if file_match and issue_match:
            findings.append({
                "doc_path": file_match.group(1).strip(),
                "severity": (sev_match.group(1).lower() if sev_match else "medium"),
                "summary": issue_match.group(1).strip(),
            })
    return findings


def parse_doc_patches(text: str) -> Dict[str, str]:
    """Returns {file_path: corrected_markdown_content}."""
    if not text or "NO_PATCH_NEEDED" in text:
        return {}

    patches = {}
    pattern = re.compile(
        r"FILE:\s*(.+?)\s*\n```(?:markdown|md|mdx|text)?\n(.*?)```", re.DOTALL
    )
    for match in pattern.finditer(text):
        path = match.group(1).strip()
        content = match.group(2)
        patches[path] = content
    return patches
