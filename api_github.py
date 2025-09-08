from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import os, requests
router = APIRouter()
API_KEY = os.environ.get("AGENT_API_KEY","")
def _read_token():
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"].strip()
    p = os.environ.get("GITHUB_TOKEN_FILE")
    if p and os.path.exists(p):
        return open(p,"r").read().strip()
    raise HTTPException(500, "GITHUB_TOKEN missing")
class IssueReq(BaseModel):
    repo: str; title: str; body: str | None = None
class PRAReq(BaseModel):
    repo: str; number: int; action: str
    comment: str | None = None; labels: list[str] | None = None
    merge_method: str | None = "squash"
def _gh(url, method="GET", payload=None):
    token = _read_token()
    r = requests.request(method, url,
        headers={"Authorization": f"Bearer {token}", "Accept":"application/vnd.github+json"},
        json=payload, timeout=30)
    return r
@router.post("/create_issue")
def create_issue(req: IssueReq, x_api_key: str = Header(...)):
    if x_api_key != API_KEY: raise HTTPException(401, "bad api key")
    r = _gh(f"https://api.github.com/repos/{req.repo}/issues","POST",{"title": req.title, "body": req.body or ""})
    return {"status": r.status_code, "json": r.json()}
@router.post("/pr_action")
def pr_action(req: PRAReq, x_api_key: str = Header(...)):
    if x_api_key != API_KEY: raise HTTPException(401, "bad api key")
    base = f"https://api.github.com/repos/{req.repo}/pulls/{req.number}"
    if req.action == "merge":
        r = _gh(base + "/merge", "PUT", {"merge_method": req.merge_method})
    elif req.action == "close":
        r = _gh(base.replace("/pulls/","/issues/"), "PATCH", {"state":"closed"})
    elif req.action == "reopen":
        r = _gh(base.replace("/pulls/","/issues/"), "PATCH", {"state":"open"})
    elif req.action == "comment":
        r = _gh(base.replace("/pulls/","/issues/") + "/comments", "POST", {"body": req.comment or ""})
    elif req.action == "update_branch":
        r = _gh(f"https://api.github.com/repos/{req.repo}/pulls/{req.number}/update-branch", "PUT", {})
        
    elif req.action == "label":
        r = _gh(base.replace("/pulls/","/issues/") + "/labels", "POST", {"labels": req.labels or []})
    else:
        raise HTTPException(400, "unknown action")
    return {"status": r.status_code, "json": r.json()}
