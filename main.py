from fastapi import FastAPI

# Пытаемся импортировать роутер /gen_code из соседнего файла.
# При запуске с `--app-dir app` модуль лежит в корне (api_gen_code),
# на некоторых окружениях может понадобиться префикс app.
try:
    from api_gen_code import router as gen_code_router  # /app/app/api_gen_code.py
except ModuleNotFoundError:
    from app.api_gen_code import router as gen_code_router  # fallback

app = FastAPI(title="Agent API")

# memory API
try:
    from api_memory import router as memory_router
except ModuleNotFoundError:
    from app.api_memory import router as memory_router

app.include_router(memory_router)

# Подключаем эндпойнт /gen_code
app.include_router(gen_code_router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# include stub endpoints for Telegram buttons
try:
    from api_stubs import router as stubs_router
except ModuleNotFoundError:
    from app.api_stubs import router as stubs_router

app.include_router(stubs_router)

# == deploy router ==
try:
    from api_deploy import router as deploy_router
    app.include_router(deploy_router)
except Exception as _e:
    pass

# == deploy debug router ==
try:
    from api_deploy_dbg import router as deploy_dbg_router
    app.include_router(deploy_dbg_router)
except Exception:
    pass

# == github router (force include) ==
from api_github import router as gh_router
app.include_router(gh_router)
