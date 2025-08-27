# CONTEXT / NEXT AGENT BRIEF

## Где мы сейчас
- Сервер развёрнут (Ubuntu 24.04, Docker, UFW, swap).
- Подняты сервисы: 
  - **Caddy** (HTTPS, прокси на agent и n8n),
  - **Agent (FastAPI)**: эндпоинт `/healthz` возвращает `{"ok": true}`,
  - **n8n**: настроены три workflow:
    - Health Check (manual) → ручная проверка /healthz
    - Telegram Basic Reply → приветствие и inline-кнопки (approve / check_healthz / reject)
    - Telegram Agent Callback → обработка нажатий кнопок, merge chat_id + HTTP, отправка результата

## Что работает
- Кнопка "Проверить агент /healthz" в Telegram → callback workflow → в чате ответ `"Агент: true"`.
- "Одобрить / Отклонить" пока отдают только заглушки.

## План (ближайшие задачи)
1. Добавить в Agent новый эндпоинт `/create_repo` (создание GitHub-репозитория и пуш скелета).
2. Привязать кнопку ✅ Одобрить к вызову этого эндпоинта через n8n.
3. Для ❌ Reject сделать ответ "Отклонено, действие отменено".
4. Добавить логирование (кто нажал, какой ответ, ссылка на результат) → сохранить в таблицу/Google Sheet.

## Как запускать
```bash
cd ~/agent_server
docker compose up -d
docker compose logs -f caddy|n8n|agent

md
