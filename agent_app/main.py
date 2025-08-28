from fastapi import FastAPI, Request, Header
from pydantic import BaseModel
from datetime import datetime
import os, json, urllib.request as u, urllib.error as e
import subprocess, shlex

app = FastAPI(title="Agent Executor", version="0.9.1")
STARTED_AT = globals().get("STARTED_AT") or datetime.utcnow().isoformat() + "Z"
globals()["STARTED_AT"] = STARTED_AT

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/status")
def status():
    return {
        "service": "agent-executor",
        "version": app.version if hasattr(app, "version") else "unknown",
        "started_at": STARTED_AT,
        "endpoints": ["/healthz", "/status", "/create_issue", "/gen_text", "/deploy_app"],
        "env": {
            "GITHUB_TOKEN_set": bool(os.environ.get("GITHUB_TOKEN")),
            "OPENAI_API_KEY_set": bool(os.environ.get("OPENAI_API_KEY")),
            "DEPLOY_SECRET_set": bool(os.environ.get("DEPLOY_SECRET")),
        }
    }

def _normalize_token(raw: str) -> str:
    if not raw: return ""
    t = raw.strip().strip('"').strip("'").replace("\n","").replace(" ","")
    try: t = t.encode("ascii","ignore").decode()
    except Exception: pass
    return t

def _run(cmd: str, cwd: str | None = None, timeout: int = 180):
    try:
        proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out.decode("utf-8", "ignore")
    except Exception as ex:
        return 127, f"EXEC ERROR: {ex} (cmd={cmd}, cwd={cwd})"

class CreateIssuePayload(BaseModel):
    token: str | None = None
    repo_full_name: str
    title: str
    body: str | None = None

@app.post("/create_issue")
def create_issue(p: CreateIssuePayload, request: Request):
    auth = request.headers.get("Authorization", "")
    header_tok = auth.split(" ",1)[1] if auth.lower().startswith("bearer ") else ""
    body_tok = p.token or ""
    safe_token = _normalize_token(header_tok or body_tok)
    if not safe_token:
        env_tok = os.environ.get("GITHUB_TOKEN", "")
        safe_token = _normalize_token(env_tok)

    url = f"https://api.github.com/repos/{p.repo_full_name}/issues"
    payload = json.dumps({"title": p.title, "body": (p.body or "")}).encode("utf-8")
    req = u.Request(url, data=payload, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {safe_token}")
    try:
        with u.urlopen(req, timeout=30) as r:
            j = json.loads(r.read().decode("utf-8"))
            return {"ok": True, "html_url": j.get("html_url"), "number": j.get("number")}
    except e.HTTPError as er:
        try: txt = er.read().decode("utf-8")
        except Exception: txt = str(er)
        return {"ok": False, "status": getattr(er,"code",None), "error": txt}

class GenTextPayload(BaseModel):
    prompt: str
    model: str | None = "gpt-4o-mini"
    max_tokens: int | None = 300
    temperature: float | None = 0.2
    api_key: str | None = None

def _pick_openai_key(api_key_body: str | None, x_openai_key: str | None, auth_header: str) -> str:
    if x_openai_key: return x_openai_key.strip()
    if api_key_body: return api_key_body.strip()
    if auth_header.lower().startswith("bearer "): return auth_header.split(" ",1)[1].strip()
    return os.environ.get("OPENAI_API_KEY","").strip()

@app.post("/gen_text")
def gen_text(p: GenTextPayload, request: Request, x_openai_key: str | None = Header(default=None)):
    key = _pick_openai_key(p.api_key, x_openai_key, request.headers.get("Authorization",""))
    if not key:
        return {"ok": False, "error": "No OpenAI API key provided"}
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": p.model or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a concise, helpful technical agent. Reply in the user's language."},
            {"role": "user", "content": p.prompt}
        ],
        "max_tokens": p.max_tokens or 300,
        "temperature": p.temperature if p.temperature is not None else 0.2
    }
    data = json.dumps(body).encode("utf-8")
    req = u.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {key}")
    try:
        with u.urlopen(req, timeout=60) as r:
            j = json.loads(r.read().decode("utf-8"))
            text = None
            if isinstance(j, dict) and "choices" in j and j["choices"]:
                msg = j["choices"][0].get("message") or {}
                text = (msg.get("content") or "").strip()
            return {"ok": True, "text": text, "raw": None if text else j}
    except e.HTTPError as er:
        try: txt = er.read().decode("utf-8")
        except Exception: txt = str(er)
        return {"ok": False, "status": getattr(er,"code",None), "error": txt}

class DeployPayload(BaseModel):
    ref: str | None = "main"
    path: str | None = None
    restart: bool | None = False

@app.post("/deploy_app")
def deploy_app(p: DeployPayload, x_deploy_secret: str | None = Header(default=None)):
    wanted = os.environ.get("DEPLOY_SECRET", "").strip()
    if wanted and (x_deploy_secret or "") != wanted:
        return {"ok": False, "error": "unauthorized"}

    repo_dir = os.path.expanduser(p.path or "~/agentcompany_sync")
    steps = []

    # ensure repo present
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        code, out = _run(f"git clone https://github.com/tokaxl74/agentcompany.git {repo_dir}")
        steps.append({"cmd":"git clone", "code":code, "out":out})

    # fetch/checkout/pull with fallback
    code, out = _run("git fetch --all", cwd=repo_dir); steps.append({"cmd":"git fetch", "code":code, "out":out})
    code, out = _run(f"git checkout {p.ref or 'main'}", cwd=repo_dir); steps.append({"cmd":"git checkout", "code":code, "out":out})
    code, out = _run("git pull --rebase --autostash", cwd=repo_dir); steps.append({"cmd":"git pull (rebase --autostash)", "code":code, "out":out})
    if code != 0:
        code2, out2 = _run("git pull", cwd=repo_dir); steps.append({"cmd":"git pull (fallback)", "code":code2, "out":out2})

    # deliver main.py
    src = os.path.join(repo_dir, "agent_app", "main.py")
    if os.path.isfile(src):
        try:
            with open(src, "rb") as fsrc, open("/app/main.py", "wb") as fdst:
                fdst.write(fsrc.read())
            steps.append({"cmd":"copy main.py -> /app/main.py", "code":0, "out":"ok"})
        except Exception as ex:
            steps.append({"cmd":"copy main.py", "code":1, "out":str(ex)})

    # optional restart (only when restart=True and host dir exists)
    cwd_dir = os.path.expanduser("~/agent_server")
    if p.restart and os.path.isdir(cwd_dir):
        code, out = _run("docker compose restart agent", cwd=cwd_dir)
        steps.append({"cmd":"docker compose restart agent", "code":code, "out":out})
    else:
        steps.append({"cmd":"docker compose restart agent", "code":0, "out":"skipped (restart=false or dir missing)"})

    return {"ok": True, "ref": p.ref or "main", "repo_dir": repo_dir, "steps": steps}


import signal

@app.post("/reload_agent")
def reload_agent(x_deploy_secret: str | None = Header(default=None)):
    wanted = os.environ.get("DEPLOY_SECRET", "").strip()
    if wanted and (x_deploy_secret or "") != wanted:
        return {"ok": False, "error": "unauthorized"}
    try:
        # Посылаем SIGHUP master-процессу gunicorn (PID 1) — воркеры перечитают код
        os.kill(1, signal.SIGHUP)
        return {"ok": True, "reloaded": True}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}
