from fastapi import FastAPI, Request, Header
from pydantic import BaseModel
import json, os
import urllib.request as u
import urllib.error as e

app = FastAPI(title="Agent Executor", version="0.8.0")

@app.get("/healthz")
def healthz():
    return {"ok": True}

# ---------- GitHub: create_issue ----------
class CreateIssuePayload(BaseModel):
    token: str | None = None
    repo_full_name: str
    title: str
    body: str | None = None

def _normalize_token(raw: str) -> str:
    if not raw: return ""
    t = raw.strip().strip('"').strip("'").replace("\n","").replace(" ","")
    try: t = t.encode("ascii","ignore").decode()
    except Exception: pass
    return t

def _preview(t: str) -> str:
    return "" if not t else f"{t[:6]}…{t[-4:]} (len={len(t)})"

@app.post("/create_issue")
def create_issue(p: CreateIssuePayload, request: Request):
    auth = request.headers.get("Authorization", "")
    header_tok = auth.split(" ",1)[1] if auth.lower().startswith("bearer ") else ""
    body_tok = p.token or ""
    safe_token = _normalize_token(header_tok or body_tok)
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
        return {"ok": False, "status": getattr(er,"code",None), "error": txt,
                "dbg": {"header_token": _preview(header_tok), "body_token": _preview(body_tok)}}

# ---------- OpenAI: gen_text ----------
class GenTextPayload(BaseModel):
    prompt: str
    model: str | None = "gpt-4o-mini"
    max_tokens: int | None = 300
    temperature: float | None = 0.2
    api_key: str | None = None  # опционально: можно передать в body

def _pick_openai_key(api_key_body: str | None, x_openai_key: str | None, auth_header: str) -> str:
    if x_openai_key: return x_openai_key.strip()
    if api_key_body: return api_key_body.strip()
    if auth_header.lower().startswith("bearer "): return auth_header.split(" ",1)[1].strip()
    env = os.environ.get("OPENAI_API_KEY", "").strip()
    return env

@app.post("/gen_text")
def gen_text(p: GenTextPayload, request: Request, x_openai_key: str | None = Header(default=None)):
    auth = request.headers.get("Authorization", "")
    key = _pick_openai_key(p.api_key, x_openai_key, auth)
    if not key:
        return {"ok": False, "error": "No OpenAI API key provided (use header Authorization: Bearer <KEY> or X-OpenAI-Key, or set OPENAI_API_KEY env)."}

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
            # универсально: старый/новый формат
            text = None
            if isinstance(j, dict):
                if "choices" in j and j["choices"]:
                    msg = j["choices"][0].get("message") or {}
                    text = (msg.get("content") or "").strip()
                elif "output" in j:
                    text = str(j["output"]).strip()
            return {"ok": True, "text": text, "raw": j if text is None else None}
    except e.HTTPError as er:
        try: txt = er.read().decode("utf-8")
        except Exception: txt = str(er)
        return {"ok": False, "status": getattr(er,"code",None), "error": txt}
