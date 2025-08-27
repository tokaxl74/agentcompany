# Handoff — Telegram Callback → Agent → GitHub/LLM

## Готово
- /create_issue (GitHub, PAT через Authorization: Bearer)
- /gen_text (OpenAI, ключ через Authorization: Bearer или OPENAI_API_KEY)
- n8n: ✅ approve → issue + ссылка; 🔍 check_healthz → ответ LLM; ❌ reject → отменено
- Answer Query a callback снимает крутилку для всех кнопок

## Чек-лист проверки
1) GET /healthz → {"ok": true}
2) POST /create_issue (через n8n кнопку ✅) → приходит ссылка на issue
3) POST /gen_text (через кнопку 🔍) → короткий ответ модели

## Дальше (последовательные шаги)
- Вынести ключи в ENV: GITHUB_TOKEN, OPENAI_API_KEY (n8n/agent)
- Добавить /deploy_app или /gen_code (следующий инкремент агента)
