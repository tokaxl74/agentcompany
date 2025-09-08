import base64, os, time, re, httpx
from typing import Optional, List, Tuple

GITHUB_API = "https://api.github.com"
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\\-_/ ]+", "", s).strip().lower().replace(" ", "-")
    return re.sub(r"-{2,}", "-", s)[:48]

async def _get_ref_sha(c: httpx.AsyncClient, owner: str, repo: str, branch: str) -> str:
    r = await c.get(f"{GITHUB_API}/repos/{owner}/{repo}/git/refs/heads/{branch}", headers=HEADERS)
    r.raise_for_status()
    return r.json()["object"]["sha"]

async def _create_branch(c: httpx.AsyncClient, owner: str, repo: str, from_sha: str, new_branch: str):
    r = await c.post(f"{GITHUB_API}/repos/{owner}/{repo}/git/refs",
                     headers=HEADERS, json={"ref": f"refs/heads/{new_branch}", "sha": from_sha})
    if r.status_code not in (201, 422):  # 422 — ветка уже есть
        r.raise_for_status()

async def _get_file_sha(c: httpx.AsyncClient, owner: str, repo: str, path: str, ref: str) -> Optional[str]:
    r = await c.get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}", headers=HEADERS, params={"ref": ref})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("sha")

async def _put_file(c: httpx.AsyncClient, owner: str, repo: str, path: str, content: str,
                    message: str, branch: str, sha: Optional[str]=None):
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {"message": message, "content": b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    r = await c.put(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}", headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()

async def _create_pr(c: httpx.AsyncClient, owner: str, repo: str, base: str, head: str, title: str, body: str) -> str:
    r = await c.post(f"{GITHUB_API}/repos/{owner}/{repo}/pulls",
                     headers=HEADERS, json={"title": title, "body": body, "base": base, "head": head})
    r.raise_for_status()
    return r.json()["html_url"]

async def create_pr_with_changes(repo_full: str, base_branch: str, pr_title: str,
                                 pr_body: str, changes: List[dict]) -> Tuple[str, str]:
    assert GH_TOKEN, "GITHUB_TOKEN is empty"
    owner, repo = repo_full.split("/", 1)
    async with httpx.AsyncClient(timeout=60) as c:
        base_sha = await _get_ref_sha(c, owner, repo, base_branch)
        branch = f"gen/{_slug(pr_title)}-{int(time.time())}"
        await _create_branch(c, owner, repo, base_sha, branch)
        for ch in changes:
            path = ch["path"]; content = ch["content"]; msg = ch.get("message") or f"update {path}"
            old_sha = await _get_file_sha(c, owner, repo, path, branch)
            await _put_file(c, owner, repo, path, content, msg, branch, sha=old_sha)
        pr_url = await _create_pr(c, owner, repo, base_branch, branch, pr_title, pr_body or "")
        return branch, pr_url
