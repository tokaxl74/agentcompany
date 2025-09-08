from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from github_pr import create_pr_with_changes
import os

API_KEY = os.environ.get("AGENT_API_KEY", "").strip()
router = APIRouter()

class Change(BaseModel):
    path: str
    content: str
    message: Optional[str] = None

class GenCodeReq(BaseModel):
    repo: str
    base_branch: str = "main"
    pr_title: str = Field(..., min_length=3)
    pr_body: Optional[str] = ""
    changes: List[Change]

@router.post("/gen_code")
async def gen_code(req: GenCodeReq, x_api_key: str = Header(default="")):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    branch, pr_url = await create_pr_with_changes(
        req.repo, req.base_branch, req.pr_title, req.pr_body or "", [c.model_dump() for c in req.changes]
    )
    return {"branch": branch, "pr_url": pr_url}
