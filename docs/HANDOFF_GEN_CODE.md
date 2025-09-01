# Handoff (core): /gen_code → GitHub PR

## Что есть
- FastAPI (uvicorn) в контейнере `agent`: /healthz, /gen_code
- /gen_code принимает JSON: {repo, base_branch, pr_title, pr_body, changes[]}
- Рабочий PR-поток проверен (последний pr_url см. в истории)

## Файлы
- agent/github_pr.py      — GitHub API: ветка, файл, PR
- agent/api_gen_code.py   — эндпойнт POST /gen_code
- agent/main.py           — FastAPI app + /healthz
- docker-compose.yml      — сервис `agent` (uvicorn ... --app-dir app)

## Секреты (в .env — не коммитим)
- AGENT_API_KEY=...
- GITHUB_TOKEN=github_pat_... (Fine-grained: Repository access=tokaxl74/agentcompany; Permissions=Contents RW, Pull requests RW)

## Быстрый smoke-тест (из контейнера):
curl -s http://127.0.0.1:8000/healthz
curl -s -X POST http://127.0.0.1:8000/gen_code -H "Content-Type: application/json" -H "X-API-Key: <KEY>" -d '{"repo":"tokaxl74/agentcompany","base_branch":"main","pr_title":"feat: test","pr_body":"from agent","changes":[{"path":"agent/hello.py","content":"def hello():\n    return {\"ok\": True}\n","message":"feat: hello"}]}'
