# Automation

Каталог `automation/` хранит конфигурацию и вспомогательные файлы для фонового workloop-процесса, который поднимает и сопровождает background tasks в проекте.

## Состав каталога

### Исполняемые файлы

- `run_workloop.sh` — каноничный shell-обёртка для запуска `astro_workloop.py` из корня проекта. Скрипт:
  - выставляет `DUCTOR_INTERAGENT_PORT` (по умолчанию `8800`),
  - выставляет `DUCTOR_AGENT_NAME` (по умолчанию `astro`),
  - выставляет `DUCTOR_CHAT_ID` (по умолчанию `833478509`),
  - переходит в `/opt/astro-project`,
  - запускает `python3 astro_workloop.py --max-running 2`.

- `log_worker_question.py` — утилита для записи вопроса от background worker в `worker_questions.yaml`, чтобы вопрос был подхвачен маршрутизацией/родительским агентом.

- `export_evidence.py` — утилита для сборки revision bundle в `test-results/evidence/<rev>/`: экспортирует свежие `.task-logs`, поддерживает дополнительные `--copy` источники и обновляет `manifest.json` + общий `manifest.revisions.json`.
- `nightly_evidence_bundle.sh` — shell-обёртка для nightly pipeline: складывает свежие task-логи, `test-results/grace-report.json`, `logs/gracectl/` и `test-results/failures/` в один revision bundle.

### YAML/JSON состояние

- `task_queue.yaml` — очередь задач для automation/workloop. Содержит метаданные задач: `id`, `title`, `status`, `depends_on`, `provider`, `model`, `acceptance_criteria`, `prompt`, `worker_task_id`, `result_summary` и `updated_at`.
- `autonomy_policy.yaml` — политика автономии: разрешённые и запрещённые действия, правила маршрутизации вопросов к архитектору и автоответы на типовые вопросы воркеров.
- `worker_questions.yaml` — накопитель открытых/закрытых вопросов от background tasks.
- `model_rr_state.json` — служебное состояние для round-robin/распределения моделей между задачами.

`cli_health` — runtime-состояние, а не конфигурация. По умолчанию `automation/cli_health.py`
и `astro_workloop.py` пишут его в `automation/.runtime/cli_health.json`; путь можно
переопределить через `SUPERVISOR_CLI_HEALTH_PATH`.

### Логи

- `workloop.log` — лог обычного запуска workloop.
- `workloop-cron.log` — лог запуска workloop из cron/system scheduler.

## Основные сценарии запуска

### 1. Запуск workloop вручную

Каноничный способ:

```bash
./automation/run_workloop.sh
```

Что делает сценарий:

1. Проставляет переменные окружения для подключения к `astro`-инстансу Ductor.
2. Запускает `astro_workloop.py` из корня репозитория.
3. Разрешает одновременно до двух активных background tasks через `--max-running 2`.

Если нужно переопределить параметры окружения, можно передать их перед запуском:

```bash
DUCTOR_INTERAGENT_PORT=8800 DUCTOR_AGENT_NAME=astro DUCTOR_CHAT_ID=833478509 ./automation/run_workloop.sh
```

### 2. Запуск workloop напрямую без shell-обёртки

Полезно для отладки:

```bash
cd /opt/astro-project
DUCTOR_INTERAGENT_PORT=8800 DUCTOR_AGENT_NAME=astro DUCTOR_CHAT_ID=833478509 \
python3 astro_workloop.py --max-running 2
```

Этот вариант эквивалентен `run_workloop.sh`, но удобен, если нужно быстро менять аргументы Python-процесса.

### 3. Логирование вопроса от worker

Если background task не может продолжать работу без уточнения, вопрос записывается так:

```bash
python3 automation/log_worker_question.py <task_id> "Текст вопроса"
```

Опционально можно указать владельца записи:

```bash
python3 automation/log_worker_question.py <task_id> "Текст вопроса" --owner worker
```

Результат:

- если `automation/worker_questions.yaml` ещё не существует, он будет создан;
- в секцию `questions` добавится новая запись со статусом `open` и UTC-временем `created_at`.

### 4. Экспорт свежих task-логов в evidence

Базовый сценарий:

```bash
python3 automation/export_evidence.py
```

Что делает утилита:

1. Сканирует один или несколько `--source` путей (по умолчанию `.task-logs`).
2. Для `fresh`-источников берёт файлы, изменённые за последние 24 часа.
3. Дополнительные `--copy` пути пакует целиком в тот же revision bundle.
4. Копирует всё в `test-results/evidence/<rev>/`.
5. Создаёт `manifest.json` со списком экспортированных файлов и обновляет общий `manifest.revisions.json` по ревизиям.

Полезные флаги:

```bash
python3 automation/export_evidence.py --hours 6
python3 automation/export_evidence.py --dest rev-2026-03-27-task-logs
python3 automation/export_evidence.py --copy test-results/grace-report.json --copy logs/gracectl
python3 automation/export_evidence.py --preserve-tree --source .task-logs --source logs/gracectl
python3 automation/export_evidence.py --dry-run
./automation/nightly_evidence_bundle.sh nightly-2026-03-27
```

Это удобно запускать после прохождения task-specific quick profile, чтобы быстро приложить свежие `.task-logs` к артефактам в `test-results/evidence`.

## Как читать automation-состояние

- Проверка текущей очереди задач: открыть `automation/task_queue.yaml`.
- Проверка зависших/неотвеченных вопросов воркеров: открыть `automation/worker_questions.yaml`.
- Проверка рамок автономии: открыть `automation/autonomy_policy.yaml`.
- Проверка логов фонового раннера: смотреть `automation/workloop.log` и `automation/workloop-cron.log`.

## Связанные файлы вне каталога

- `astro_workloop.py` — основной Python runner, который использует данные из `automation/`.
- `AGENTS.md` — общие правила работы агента, тестовые профили и протоколы.
- `tools/task_tools/ask_parent.py` — каноничный способ запросить уточнение у родительского агента, если задача заблокирована.
