# AgentCompany — Companion Agent Stack

Этот репозиторий содержит:
- **infra/** — docker-compose.yml, Caddyfile (инфраструктура сервера)
- **agent_app/** — код агента (FastAPI, /healthz)
- **n8n/workflows/** — экспорт воркфлоу (Basic Reply, Agent Callback, Health Check)
- **PROMPT_NEXT_AGENT.md** — бриф для следующего агента (handoff)

## Запуск
```bash
cd infra
cp .env.example .env
docker compose up -d
