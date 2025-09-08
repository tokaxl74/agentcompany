📌 Текущее положение

Nikolai 3.0 и AI Crypto Analyst физически есть (репозитории, сервера подготовлены), но они не подключены и не работают → ждут, пока Telegram-агент будет готов их подхватить.

Telegram-агент уже умеет:

делать PR, issue, деплой,

управлять сервером Николая (infra),

и будет расширяться кнопками (Docs, Status, Logs, Ask/Explain).

🧠 Идея с моделями GPT

Очень правильный подход — разделить задачи по «уровню интеллекта»:

GPT-5 (дорого, но мощно)
Использовать для:

Архитектуры проектов.

Проработки бизнес-логики и концепции.

Сложного кода (генерация целых модулей, CI/CD).

Аналитики и стратегии.

GPT-4 или более дешёвые LLM
Использовать для:

Обработки простых запросов (Ask/Explain, эхо-ответы, FAQ).

Черновых задач (парсинг, рерайт документации, логов).

Вспомогательных workflow (проверка статуса, лёгкая валидация).

👉 Таким образом, агент будет умным и экономным одновременно: дорогой мозг включаем только там, где действительно нужно.

🚦 Что сделать дальше

Довести Telegram-агента до production-версии

Fix .env (N8N_ENCRYPTION_KEY, HOST).

Добавить кнопки Docs / Status / Logs.

Сделать Ask/Explain через GPT (с прокси выбора модели: GPT-5 → для сложных запросов, GPT-4 → для простых).

Подключить Николая и Crypto Analyst к агенту

Добавить их как проекты в projects.json.

Настроить кнопки Deploy / Status для каждого.

Постепенно через агента дописывать их логику.

Закрепить принцип «экономия токенов»

Ввести маршрутизацию: если запрос «простая справка» → дешёвая модель, если «архитектура/код» → GPT-5.

Это делается на уровне FastAPI-агента (условие: по типу задачи выбираем endpoint).

Зафиксировать это как стандарт

В GitHub в репозитории агентcompany прописать:

Политика выбора моделей.

Стратегия интеграции проектов (Nikolai / Crypto Analyst).

Дорожная карта: «Agent → Подключение проектов → Создание приложений». ROADMAP — Telegram-Агент «One-Button DevOps»
1) Зачем

Делаем универсального Telegram-агента, который:

допиливает текущие продукты (Nikolai 3.0, AI Crypto Analyst),

управляет деплоем/статусом/логами в один клик,

дальше — создаёт новые приложения по тексту (и голосу), а мы монетизируем функционал.

2) Текущее положение (зафиксировано)

n8n (Агент): поднят, workflow Telegram Agent Callback 2 активен.

Кнопки деплоя (есть):

Deploy agentcompany → деплой FastAPI-агента (локально).

Deploy infra-n8n-alkola → рестарт прод-инфры Николая (SSH на 46.243.181.154).

БД n8n: ./n8n_data/database.sqlite (права 1000:1000, размер ~7.3 MB).

Домены:

agent.alcryptan.online → FastAPI-агент

n8n.alcryptan.online → n8n (через Caddy)

Файл реестра проектов (agent/projects.json, актуальные ключи):

{
  "agentcompany": {
    "repo": "tokaxl74/agentcompany",
    "ref": "main",
    "subdir": "agent",
    "target": "/app"
  },
  "infra-n8n-alkola": {
    "repo": "tokaxl74/infra-n8n-alkola",
    "ref": "main",
    "subdir": "",
    "target": "/root/infra-n8n-alkola",
    "compose": "/root/n8n_setup/docker-compose.yml",
    "host": "46.243.181.154"
  },
  "nikolai-docs": {
    "repo": "tokaxl74/n8n-docs-AIComp",
    "ref": "main",
    "subdir": "",
    "target": "/opt/n8n_docs"
  }
}

3) Архитектура (в 1 абзац)

Telegram (кнопки) → n8n (workflow-логика) → FastAPI-агент (роуты /deploy_app, /gen_code, /gen_text) → GitHub (код/PR/доки) → Серверы (Docker/Caddy/Postgres) → Приложения (Nikolai, Crypto Analyst, новые).
Модели LLM выбираются динамически (см. п.5).

4) Кнопки и их назначение (must-have)

Deploy agentcompany — обновляет/перезапускает FastAPI-агента (локально).

Deploy infra-n8n-alkola — SSH на VM Николая, git pull → docker compose pull → up -d.

Deploy Nikolai Docs — тянет tokaxl74/n8n-docs-AIComp и выкладывает в /opt/n8n_docs.

Status Nikolai — SSH docker ps и docker compose images → ответ в <pre>…</pre>.

Logs Nikolai — хвост /tmp/deploy_infra.log или compose logs --tail N.

Привязка в n8n (HTTP Request):

URL: http://agent:8000/deploy_app

Headers: X-API-KEY: {{$env.AGENT_API_KEY}}, Content-Type: application/json

Body (JSON):

{"project":"nikolai-docs","pull":true}

{"project":"infra-n8n-alkola","pull":true,"rebuild":false,"logs_tail":20}

5) Политика выбора LLM (умно и экономно)

Идея: дорогой интеллект — там, где он окупается; дешёвый — где хватает.

GPT-5 (дорого, мощно)
Используем для: архитектуры, сложного кода/проектирования, разборов требований, критичных решений.
Параметры (пример): temperature: 0.2, max_tokens: 2–4k.

GPT-4 / более дешёвые
Используем для: FAQ/Ask/Explain, черновых текстов, валидации простых ответов, лёгкой аналитики.
Параметры: temperature: 0.3–0.5, max_tokens: 500–1000.

Маршрутизатор (псевдокод):

if task.type in {"architecture","critical_code","system_design"}:
    model = "gpt-5"
elif task.type in {"docs","ask","status","logs","minor_fix"}:
    model = "gpt-4-mini"
else:
    model = "gpt-4"


Где реализуем: в FastAPI-агенте (/gen_text), добавив поле mode/task_type.

6) Чек-лист .env (агент/инфра)

Обязательные:

# общий
AGENT_API_KEY=<случайный_ключ_для_X-API-KEY>
GITHUB_TOKEN=<PAT с правами repo:RW, PR:RW>

# n8n (агентский)
N8N_ENCRYPTION_KEY=<длинный_ключ>
N8N_HOST=n8n.alcryptan.online
LETSENCRYPT_EMAIL=alcryptobol@gmail.com
AGENT_HOST=agent.alcryptan.online


Никогда не коммитим секrets в Git.

7) План ближайших работ (2–3 дня)

A. Кнопки для Николая (в n8n):

 Добавить Deploy Nikolai Docs (как выше).

 Добавить Status Nikolai → /status {"project":"infra-n8n-alkola","details":true}.

 Добавить Logs Nikolai → /logs {"project":"infra-n8n-alkola","n":120}.

B. Ask/Explain → реальная LLM

 В agent/api_text.py подключить маршрутизатор моделей (п.5).

 В n8n заменить echo-узлы на вызов /gen_text.

C. Документация/фикс состояния

 Обновить docs/HANDOFF_NEXT.md (новые кнопки и SSH-режим деплоя).

 Экспортировать workflow → docs/wf_all.json.

 Этот файл docs/ROADMAP.md закоммитить.

8) Среднесрочный план (2–4 недели)

Создать новое приложение (кнопка):
Telegram → описание/голос → GPT → GitHub repo → PR → деплой на поддомен → кнопки управления.

Монетизация:

Николай: подписки/премиум (Telegram + web, ЮKassa/Stripe/USDT).

Crypto Analyst: платные каналы.

Мониторинг: health-чек, диски, ошибки → алерты в TG.

Шаблоны проектов: FastAPI, React, Telegram-бот (быстрый старт).

9) Операционный «Runbook» администратора

Обновить агента: Deploy agentcompany.

Перезапустить Николая: Deploy infra-n8n-alkola.

Обновить доки Николая: Deploy Nikolai Docs.

Проверить здоровье: /healthz (агент), Status Nikolai (инфра).

Получить логи деплоя: Logs Nikolai.

10) Definition of Done (текущая фаза)

 В Telegram доступны 3 кнопки деплоя + 2 сервисные (Status/Logs).

 /gen_text работает через маршрутизатор моделей.

 docs/HANDOFF_NEXT.md, docs/ROADMAP.md, docs/wf_all.json обновлены.

 n8n и агент стабильно поднимаются из .env и ./n8n_data.

11) Команды для фиксации в GitHub
# в репо tokaxl74/agentcompany
git pull
mkdir -p docs
# создать / обновить файл docs/ROADMAP.md содержимым этой страницы
git add docs/ROADMAP.md docs/HANDOFF_NEXT.md docs/wf_all.json
git commit -m "roadmap: зафиксировано текущее состояние; кнопки Николая; LLM-роутинг; план работ"
git push
