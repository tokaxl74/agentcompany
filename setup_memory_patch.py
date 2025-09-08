import io, re, sys, os, sqlite3, json
p = "/app/main.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

if "api_memory" not in s:
    s = s.replace(
        'app = FastAPI(title="Agent API")',
        'app = FastAPI(title="Agent API")\n\n# memory API\ntry:\n    from api_memory import router as memory_router\nexcept ModuleNotFoundError:\n    from app.api_memory import router as memory_router\n\napp.include_router(memory_router)'
    )
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

os.makedirs("/app/data", exist_ok=True)
db_path = "/app/data/agent_memory.sqlite"
con = sqlite3.connect(db_path)
con.execute("PRAGMA journal_mode=WAL;")
con.execute("""CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT DEFAULT (datetime('now')),
    project TEXT,
    kind TEXT,
    text TEXT,
    meta TEXT
)""")
con.execute("""CREATE TABLE IF NOT EXISTS agent_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT DEFAULT (datetime('now')),
    workflow TEXT,
    node TEXT,
    status TEXT,
    error TEXT
)""")
con.commit()
print("patched & db ready:", db_path)
