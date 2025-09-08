from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
import os, json, shlex, time

try:
    import paramiko
except Exception:
    paramiko = None

router = APIRouter()
API_KEY = os.getenv("AGENT_API_KEY","")
SSH_KEY_PATH = os.getenv("DEPLOY_SSH_KEY","/run/secrets/deploy_ssh_key")
try:
    ALLOW = json.loads(os.getenv("DEPLOY_TARGETS_JSON","{}"))
except Exception:
    ALLOW = {}

class DeployReq(BaseModel):
    target: str = Field(..., description="ключ из allow-list")
    services: list[str] | None = None
    pull: bool = True
    build: bool = False
    compose_dir: str | None = None

def _ssh_exec(host: str, cmd: str, user: str = "deploy", timeout: int = 900):
    if paramiko is None:
        raise RuntimeError("paramiko not installed")
    if not os.path.exists(SSH_KEY_PATH):
        raise RuntimeError("DEPLOY_SSH_KEY missing")
    k = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname=host, username=user, pkey=k, timeout=20)
    try:
        _, out, err = c.exec_command(cmd, timeout=timeout)
        stdout = out.read().decode(errors="ignore")
        stderr = err.read().decode(errors="ignore")
        rc = out.channel.recv_exit_status()
        return rc, stdout, stderr
    finally:
        c.close()

@router.post("/deploy_app")
def deploy_app(req: DeployReq, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "bad api key")
    if not isinstance(ALLOW, dict) or req.target not in ALLOW:
        raise HTTPException(400, "target not allowed")

    t = ALLOW[req.target]
    host = t["host"]; user = t.get("user","deploy")
    compose_dir = shlex.quote(req.compose_dir or t["compose_dir"])

    # if services not provided -> use default_services from allow-list (if any)
    svcs = req.services if req.services is not None else t.get("default_services", [])
    services = " ".join(shlex.quote(s) for s in svcs)

    steps = []
    if req.pull:  steps.append(f"docker compose pull {services}".strip())
    if req.build: steps.append(f"docker compose build {services}".strip())
    steps.append(f"docker compose up -d --no-recreate {services}".strip())

    # first try: up --no-recreate
    cmd1 = f"cd {compose_dir} && {' && '.join([s for s in steps if s])} && docker compose ps"
    rc, out, err = _ssh_exec(host, cmd1, user=user)

    # fallback: if name conflict, do restart and ps
    if rc != 0 and ("already in use by container" in (out.lower()+err.lower())) and services:
        cmd2 = f"cd {compose_dir} && docker compose restart {services} || true && docker compose ps"
        rc2, out2, err2 = _ssh_exec(host, cmd2, user=user)
        rc, out, err = rc2, out2, err2

    return {"target": req.target, "host": host, "rc": rc, "stdout": out[-6000:], "stderr": err[-2000:], "ts": int(time.time())}
