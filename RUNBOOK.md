# Runbook по запуску AstroSaaS (MVP)

Данный документ описывает процесс развертывания и настройки сервиса AstroSaaS для Stage и Production окружений.

## 1. Конфигурация окружения

Скопируйте `.env.example` в `.env` и заполните обязательные значения.

### Обязательные переменные:
- `ENVIRONMENT`: `production` или `stage`.
- `DATABASE_URL`: Строка подключения к PostgreSQL.
- `TELEGRAM_BOT_TOKEN`: Токен от @BotFather.
- `WEBAPP_URL`: Публичный URL фронтенда (например, `https://astrograce.ru`).
- `BOT_ADMIN_IDS`: Список ID Telegram через запятую, имеющих доступ к `/api/admin/*`.
- `YOOKASSA_SHOP_ID`: ID магазина ЮKassa.
- `YOOKASSA_SECRET_KEY`: Секретный ключ ЮKassa.
- `OPENROUTER_API_KEY`: Ключ API для генерации отчетов через LLM.

## 2. Развертывание инфраструктуры

### Docker Compose
```bash
docker compose -f docker-compose.yml up -d --build
```

## 3. Инициализация базы данных

Запустите миграции для обновления схемы:
```bash
docker exec astro-project-backend-1 python scripts/run_migrations.py
```

## 4. Проверка работоспособности

1. **Health Check:** Проверьте `https://ваш-домен/health` (должно вернуть `{"status": "ok"}`).
2. **Бот:** Напишите `/start` боту. Он должен открыть Mini App.
3. **Smoke Test:** Запустите скрипт для полной проверки цикла генерации:
   ```bash
   docker exec astro-project-backend-1 python tests/smoke_launch.py
   ```

## 5. E2E Тестирование (Frontend)

Для проверки целостности фронтенда и визуальной регрессии используйте канонический способ запуска через Playwright контейнер:

```bash
# Запуск всех тестов
./scripts/run_e2e.sh

# Обновление скриншотов (visual regression baseline)
./scripts/run_e2e.sh --update-snapshots
```

Команда автоматически использует `docker-compose.e2e.yml` и подключается к запущенному dev-серверу фронтенда.

## 6. Особенности режимов (Mock & Dev)

- **Mock-режим:** Включается добавлением `?mock=1` в URL WebApp. Работает ТОЛЬКО если `ENVIRONMENT=development` или если `mock_telegram_user=1` установлено в sessionStorage (для E2E).
- **Админка:** Доступна по адресу `/admin/dashboard`. Требует, чтобы ваш Telegram ID был в списке `BOT_ADMIN_IDS`.

## 6. Квоты и ограничения

- **Trial:** Новые пользователи получают 14 дней доступа.
- **Хорары:** 1 бесплатный вопрос в неделю для пользователей с подпиской/триалом. Лимит сбрасывается каждый понедельник в 00:00 по местному времени пользователя. Дополнительные вопросы требуют покупки кредитов.