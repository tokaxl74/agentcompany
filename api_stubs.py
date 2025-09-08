from fastapi import APIRouter, Header, HTTPException
from typing import Optional, List, Dict, Any

router = APIRouter()

def _auth(x_api_key: Optional[str] = Header(default=None, alias="X-API-KEY")):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY")
    return True

@router.post("/gen_text")
def gen_text(payload: Dict[str, Any], x_ok: bool = _auth()):
    prompt = str(payload.get("prompt", "")).strip()
    return {"ok": True, "text": f"echo: {prompt}"}

@router.post("/create_issue_stub")
def create_issue(payload: Dict[str, Any], x_ok: bool = _auth()):
    repo = payload.get("repo", "")
    title = payload.get("title", "")
    body = payload.get("body", "")
    labels = payload.get("labels", [])
    return {
        "ok": True,
        "action": "create_issue",
        "issue": {"url": f"https://github.com/{repo}/issues/1", "title": title, "labels": labels},
        "echo": {"body": body},
    }

@router.post("/pr_action_stub")
def pr_action(payload: Dict[str, Any], x_ok: bool = _auth()):
    repo = payload.get("repo", "")
    number = payload.get("number", 0)
    action = payload.get("action", "comment")
    comment = payload.get("comment", "")
    return {
        "ok": True,
        "action": "pr_action",
        "result": {"repo": repo, "number": number, "performed": action, "comment": comment},
    }

@router.post("/deploy_app_stub")
def deploy_app(payload: Dict[str, Any], x_ok: bool = _auth()):
    project = payload.get("project", "")
    pull = bool(payload.get("pull", False))
    rebuild = bool(payload.get("rebuild", False))
    services = payload.get("services", [])
    return {
        "ok": True,
        "action": "deploy_app",
        "job_id": "stub-0001",
        "accepted": True,
        "params": {"project": project, "pull": pull, "rebuild": rebuild, "services": services},
    }
