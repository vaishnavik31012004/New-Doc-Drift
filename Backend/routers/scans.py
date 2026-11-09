import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal, Repository, Scan, Finding, ScanStatus
from schemas import ScanCreateRequest, ScanOut, CreatePRRequest
from services import github_service, vector_store
from services.ws_manager import manager
from agents.pipeline import run_pipeline_sync
from agents.parsers import parse_drift_findings, parse_doc_patches

router = APIRouter(prefix="/api/scans", tags=["scans"])


def _run_scan(scan_id: int):
    """Runs entirely in a background thread. Uses its own DB session because
    the request-scoped session is already closed by the time this executes.
    """
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        repo = db.get(Repository, scan.repository_id)
        token = repo.github_token

        def progress(agent_name: str, status: str):
            manager.broadcast_threadsafe(scan_id, {
                "type": "agent_progress", "agent": agent_name, "status": status,
            })

        # 1. Fetch the real commit diff from GitHub
        scan.status = ScanStatus.analyzing_diff
        db.commit()
        manager.broadcast_threadsafe(scan_id, {"type": "status", "status": scan.status.value})

        diff = github_service.get_commit_diff(repo.owner, repo.name, scan.commit_sha, token)
        scan.commit_message = diff["message"]
        db.commit()

        # 2. Index the repo's current docs for RAG (fresh each scan -> always current)
        scan.status = ScanStatus.matching_docs
        db.commit()
        manager.broadcast_threadsafe(scan_id, {"type": "status", "status": scan.status.value})

        doc_paths = github_service.list_doc_files(repo.owner, repo.name, token)
        docs = {p: github_service.get_file_content(repo.owner, repo.name, p, token) for p in doc_paths}
        vector_store.index_repo_docs(repo.full_name, docs)

        # 3. Run the 3-agent ADK pipeline
        scan.status = ScanStatus.drafting_patch
        db.commit()
        outputs = run_pipeline_sync(
            repo_full_name=repo.full_name,
            commit_message=diff["message"],
            diff_text=diff["diff_text"],
            github_token=token,
            on_progress=progress,
        )
        scan.diff_analysis = outputs.get("diff_analysis")
        db.commit()

        # 4. Parse structured findings + patches, persist as rows
        findings = parse_drift_findings(outputs.get("drift_findings", ""))
        patches = parse_doc_patches(outputs.get("doc_patch", ""))
        for f in findings:
            db.add(Finding(
                scan_id=scan.id,
                doc_path=f["doc_path"],
                severity=f["severity"],
                summary=f["summary"],
                suggested_patch=patches.get(f["doc_path"]),
            ))

        scan.status = ScanStatus.completed
        scan.completed_at = dt.datetime.utcnow()
        db.commit()
        manager.broadcast_threadsafe(scan_id, {"type": "status", "status": scan.status.value})

    except Exception as e:
        scan = db.get(Scan, scan_id)
        if scan:
            scan.status = ScanStatus.failed
            scan.error_message = str(e)
            db.commit()
        manager.broadcast_threadsafe(scan_id, {"type": "status", "status": "failed", "error": str(e)})
    finally:
        db.close()


@router.post("", response_model=ScanOut)
def create_scan(payload: ScanCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    repo = db.get(Repository, payload.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scan = Scan(repository_id=repo.id, commit_sha=payload.commit_sha, status=ScanStatus.pending)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(_run_scan, scan.id)
    return scan


@router.get("", response_model=list[ScanOut])
def list_scans(repository_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Scan).order_by(Scan.created_at.desc())
    if repository_id:
        q = q.filter(Scan.repository_id == repository_id)
    return q.all()


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/{scan_id}/create-pr")
def create_pr(scan_id: int, payload: CreatePRRequest, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    repo = db.get(Repository, scan.repository_id)

    findings = db.query(Finding).filter(Finding.id.in_(payload.finding_ids), Finding.scan_id == scan_id).all()
    if not findings:
        raise HTTPException(status_code=400, detail="No matching findings for this scan")

    file_updates = [
        {"path": f.doc_path, "new_content": f.suggested_patch}
        for f in findings if f.suggested_patch
    ]
    if not file_updates:
        raise HTTPException(status_code=400, detail="Selected findings have no drafted patch content")

    branch_name = payload.branch_name or f"doc-drift-guardian/{scan.commit_sha[:7]}"
    title = payload.pr_title or f"docs: fix drift from commit {scan.commit_sha[:7]}"
    body = "Automatically drafted by Doc-Drift Guardian.\n\n" + "\n".join(
        f"- **{f.doc_path}** ({f.severity}): {f.summary}" for f in findings
    )

    try:
        pr_url = github_service.create_pull_request(
            repo.owner, repo.name, branch_name, file_updates, title, body, repo.github_token,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create PR: {e}")

    for f in findings:
        f.pr_url = pr_url
    db.commit()

    return {"pr_url": pr_url}
