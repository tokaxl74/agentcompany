from fastapi import APIRouter, Header
import os, json, paramiko, shlex, traceback

router = APIRouter()
def j(v): 
    try: return json.dumps(v, ensure_ascii=False)
    except: return str(v)

@router.post("/deploy_app_dbg")
def deploy_app_dbg(x_api_key: str = Header(None)):
    info = {"step":"start"}
    try:
        API_KEY = os.getenv("AGENT_API_KEY","")
        info["api_key_set"] = bool(API_KEY)
        if not x_api_key or x_api_key != API_KEY:
            info["bad_key"] = True
            return {"ok": False, "where":"auth", "info": info}

        # parse allow-list
        raw = os.getenv("DEPLOY_TARGETS_JSON","{}")
        allow = json.loads(raw)
        info["allow_keys"] = list(allow.keys())
        t = allow.get("infra-n8n-alkola") or next(iter(allow.values()), None)
        if not t:
            return {"ok": False, "where":"allow", "info": info}

        host = t["host"]; user = t.get("user","deploy")
        cdir = t.get("compose_dir","/home/deploy/agent_server")
        info.update({"host": host, "user": user, "compose_dir": cdir})

        key_path = os.getenv("DEPLOY_SSH_KEY","/run/secrets/deploy_ssh_key")
        info["key_exists"] = os.path.exists(key_path)
        if not info["key_exists"]:
            return {"ok": False, "where":"ssh_key_missing", "info": info}

        k = paramiko.Ed25519Key.from_private_key_file(key_path)
        c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(hostname=host, username=user, pkey=k, timeout=10)
        try:
            # 1) docker path
            _,o,e = c.exec_command("which docker || command -v docker || echo NO_DOCKER", timeout=10)
            info["docker_path"] = o.read().decode().strip() or e.read().decode().strip()
            # 2) compose ps в каталоге
            cmd = f"cd {shlex.quote(cdir)} && docker compose ps"
            _,o,e = c.exec_command(cmd, timeout=60)
            info["compose_rc"] = o.channel.recv_exit_status()
            info["compose_out_tail"] = (o.read().decode(errors='ignore') or '')[-400:]
            info["compose_err_tail"] = (e.read().decode(errors='ignore') or '')[-200:]
        finally:
            c.close()

        return {"ok": True, "info": info}
    except Exception as ex:
        info["exc"] = repr(ex)
        info["tb"] = traceback.format_exc()[-1200:]
        return {"ok": False, "where":"exception", "info": info}
