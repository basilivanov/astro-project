# Dev vs Prod Flow

## Цель

Этот документ фиксирует текущий рабочий процесс для разработки и прод-выкатки в репозитории `astro-project`, чтобы было понятно:
- где идёт обычная разработка;
- что считается production-веткой;
- какие проверки обязательны перед acceptance и перед выкаткой;
- что нужно для публикации/синхронизации проекта с GitHub.

## 1. Текущее состояние Git/GitHub

На дату `2026-03-27` в репозитории уже настроен GitHub remote:
- remote: `origin`
- URL: `git@github.com:basilivanov/astro-project.git`

Текущая production-ветка:
- `prod-release-20260327`

Практический смысл текущего состояния:
- GitHub-репозиторий уже существует и подключен;
- production фиксируется отдельной release-веткой, а не «любой последней локальной веткой»;
- при необходимости можно публиковать новые изменения в GitHub через обычный `git push origin <branch>`.

### Snapshot bot

Под `snapshot bot` здесь удобно понимать бота/агента, который периодически делает рабочие снимки состояния проекта, документов и/или промежуточных задач. Для Git-процесса это означает:
- бот не заменяет обычный release-flow;
- source of truth для кода и релизного состояния остаётся Git/GitHub;
- production-состояние должно быть выражено веткой/коммитом в GitHub, а не только локальным snapshot.

Итого:
- snapshots полезны как операционный след;
- GitHub-ветка `prod-release-20260327` — это опорная точка production-состояния.

## 2. Как разделяем dev и prod

### Роли веток

Рекомендуемая практическая схема для текущего проекта:
- `master` — рабочая dev-ветка / основная ветка интеграции;
- feature/task branches — короткоживущие ветки под отдельные задачи;
- `prod-release-20260327` — production-ветка, в которую попадает только то, что готово к выкладке.

Если работать без лишней бюрократии, поток выглядит так:
1. Разработка идёт в `master` или в короткой feature-ветке от `master`.
2. После завершения задачи изменения проходят acceptance-проверки.
3. После acceptance готовый набор коммитов переносится в `prod-release-20260327`.
4. Ветка `prod-release-20260327` считается кандидатом на выкладку и production-истиной.

### Что считаем dev

`dev` — это всё, что ещё можно дорабатывать:
- локальная работа разработчика;
- незавершённые feature/task branches;
- `master`, пока изменения не подтверждены как production-ready.

### Что считаем prod

`prod` — это состояние ветки `prod-release-20260327`, которое:
- прошло обязательные acceptance-проверки;
- готово к push в GitHub;
- готово к фактической выкладке.

## 3. Acceptance: чем проверяем dev перед переносом в prod

Для этого репозитория уже зафиксированы канонические профили проверки.

### Backend quick

Обязательная быстрая проверка backend-логики:

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
```

Когда использовать:
- после любой существенной backend-правки;
- перед фиксацией acceptance по задаче;
- перед переносом изменений в production-ветку.

### Frontend quick / targeted E2E

Для фронтенда и пользовательских сценариев используем Playwright только через контейнерный wrapper:

```bash
./scripts/run_e2e.sh --last-failed
```

или точечно:

```bash
./scripts/run_e2e.sh e2e/<file>.spec.ts -g "<case>"
```

Когда использовать:
- после существенной frontend-правки;
- когда задача затрагивает UI, переходы, формы, рендеринг, acceptance flow;
- для быстрого перепрогона только затронутых сценариев.

### Smoke profile

Перед пометкой изменения как готового к выкатке используем smoke-набор:

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts
```

Практический смысл smoke:
- подтверждает, что backend quick зелёный;
- подтверждает, что ключевые пользовательские и административные сценарии не сломаны;
- даёт минимально-достаточную уверенность перед prod push.

## 4. Рекомендуемый flow: от dev к prod

### Базовый сценарий

1. Сделать изменения в `master` или feature-ветке.
2. Прогнать acceptance для затронутого слоя:
   - backend: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
   - frontend: `./scripts/run_e2e.sh --last-failed` или точечные E2E
3. Перед выкаткой прогнать smoke-профиль.
4. Перенести готовые коммиты в `prod-release-20260327`.
5. Запушить production-ветку в GitHub.
6. После push убедиться, что smoke/операционный контроль остаются зелёными.

### Что именно значит «выкатить» сейчас

В текущем процессе выкладка описывается просто:
- production-изменение = изменения, попавшие в `prod-release-20260327`;
- publish step = `git push origin prod-release-20260327`;
- release confidence = успешный smoke.

То есть минимальный рабочий deploy-flow:

```bash
git checkout prod-release-20260327
git push origin prod-release-20260327
```

После этого обязательно:
- убедиться, что smoke-проверки выполнены на актуальном состоянии;
- при наличии внешнего окружения/сервера использовать именно эту ветку как источник deploy.

## 5. Как использовать GitHub для проекта

### SSH-ключ

Чтобы пушить в GitHub по SSH, на машине должен быть настроен ключ.

Базовая проверка:

```bash
ssh -T git@github.com
```

Если ключа нет, нужен стандартный поток:
1. сгенерировать SSH key;
2. добавить public key в GitHub account;
3. проверить доступ командой `ssh -T git@github.com`.

### Remote origin

В проекте уже настроен `origin`:

```bash
git remote -v
```

Ожидаемое значение:

```bash
origin  git@github.com:basilivanov/astro-project.git (fetch)
origin  git@github.com:basilivanov/astro-project.git (push)
```

Если remote когда-либо потребуется перенастроить:

```bash
git remote set-url origin git@github.com:basilivanov/astro-project.git
```

### Публичность репозитория

Для выгрузки проекта в GitHub технически достаточно:
- существующего репозитория;
- доступа по SSH;
- корректного `origin`;
- нужной ветки локально.

Вопрос public/private решается в настройках GitHub-репозитория:
- `private` — если в проекте есть внутренние наработки, чувствительные workflow или закрытая бизнес-логика;
- `public` — если проект можно показывать внешне и в истории нет чувствительных данных.

Перед переключением в public стоит отдельно проверить:
- нет ли секретов в истории Git;
- нет ли приватных `.env`/ключей/токенов в tracked-файлах;
- не попали ли в репозиторий локальные артефакты, дампы, логи, пользовательские данные.

## 6. Что нужно, чтобы «выгрузить проект в GH»

Минимальный чеклист:
- GitHub repository существует;
- `origin` указывает на нужный GitHub repo;
- SSH-доступ работает;
- локально есть нужная ветка (`master` для dev, `prod-release-20260327` для prod);
- acceptance/smoke зелёные для той версии, которую публикуем;
- выполняется push нужной ветки.

Пример для production:

```bash
git checkout prod-release-20260327
git push origin prod-release-20260327
```

Пример для dev-синхронизации:

```bash
git checkout master
git push origin master
```

## 7. Короткая политика команды

Если формализовать в одном блоке:
- разработка идёт в `master` и/или feature-ветках;
- production живёт в `prod-release-20260327`;
- acceptance минимум = `scripts/pipeline.py` для backend + targeted/quick E2E для frontend;
- перед prod push обязателен smoke;
- публикация в GitHub = push соответствующей ветки в `origin`;
- для внешнего deploy источником должна быть production-ветка, а не случайное локальное состояние.


## Auth runtime lanes

- Production consumer auth lane: signed Telegram WebApp initData only.
- Mock Telegram lane: local development and deterministic Playwright harness only.
- Guest/no-Telegram lane: public entry only, without premium authenticated guarantees.
- Dev/test bypasses in backend are non-production helpers and must not redefine the MVP product contract.

A release-ready MVP handoff cannot rely only on mock Telegram proofs for authenticated consumer routes.
