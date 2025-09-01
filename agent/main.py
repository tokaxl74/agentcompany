from fastapi import FastAPI

# Пытаемся импортировать роутер /gen_code из соседнего файла.
# При запуске с `--app-dir app` модуль лежит в корне (api_gen_code),
# на некоторых окружениях может понадобиться префикс app.
try:
    from api_gen_code import router as gen_code_router  # /app/app/api_gen_code.py
except ModuleNotFoundError:
    from app.api_gen_code import router as gen_code_router  # fallback

app = FastAPI(title="Agent API")

# Подключаем эндпойнт /gen_code
app.include_router(gen_code_router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
