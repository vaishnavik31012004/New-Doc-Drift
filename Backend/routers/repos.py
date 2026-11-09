from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db, Repository
from schemas import RepoConnectRequest, RepositoryOut, CommitOut
from services import github_service

router = APIRouter(prefix="/api/repos", tags=["repositories"])


@router.post("", response_model=RepositoryOut)
def connect_repo(payload: RepoConnectRequest, db: Session = Depends(get_db)):
    full_name = f"{payload.owner}/{payload.name}"
    try:
        meta = github_service.get_repo_metadata(payload.owner, payload.name, payload.github_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not access repository: {e}")

    existing = db.query(Repository).filter(Repository.full_name == full_name).first()
    if existing:
        existing.description = meta["description"]
        existing.default_branch = meta["default_branch"]
        if payload.github_token:
            existing.github_token = payload.github_token
        db.commit()
        db.refresh(existing)
        return existing

    repo = Repository(
        owner=payload.owner,
        name=payload.name,
        full_name=full_name,
        default_branch=meta["default_branch"],
        description=meta["description"],
        github_token=payload.github_token,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("", response_model=list[RepositoryOut])
def list_repos(db: Session = Depends(get_db)):
    return db.query(Repository).order_by(Repository.created_at.desc()).all()


@router.get("/{repo_id}/commits", response_model=list[CommitOut])
def get_commits(repo_id: int, limit: int = 20, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    try:
        commits = github_service.list_recent_commits(repo.owner, repo.name, repo.github_token, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e}")
    return commits


@router.delete("/{repo_id}")
def remove_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    db.delete(repo)
    db.commit()
    return {"ok": True}
