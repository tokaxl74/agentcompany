# Handoff — Agent endpoints (update)

## Эндпоинты
- GET /healthz — {"ok": true}
- GET /status — сервис/версия/аптайм/наличие ключей
- POST /create_issue — GitHub Issues, токен берётся из Authorization: Bearer или из ENV GITHUB_TOKEN (fallback)
- POST /gen_text — OpenAI Chat Completions, ключ берётся из Authorization: Bearer или из ENV OPENAI_API_KEY (fallback)

## Проверка
1) curl -sS https://agent.<домен>/status
2) /create_issue вызывается из n8n без токена — берётся из ENV
3) /gen_text вызывается из n8n без токена — берётся из ENV
