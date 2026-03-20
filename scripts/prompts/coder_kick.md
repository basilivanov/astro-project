# ROLE: CODER (Gemini in tmux session `astro`)
#
# TASK: Выполни следующую итерацию разработки по Task.md.
#
# Protocol:
# 1) Прочитай `AGENTS.md` и `Task.md`.
# 2) Найди следующую задачу P0 со статусом `[ ]` и выполни её.
# 3) После изменений ОБЯЗАТЕЛЬНО прогони тесты:
#    - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
#    - `./scripts/run_e2e.sh` (или минимум `./scripts/run_e2e.sh --last-failed`, если менялся только фронт)
# 4) Обнови `Task.md`:
#    - отметь задачу `[x]`
#    - заполни `DONE / Files / Tests / Evidence / Risks/Open`
#    - добавь отдельной строкой маркер `READY_FOR_REVIEW`
#
# Notes:
# - Не удаляй задачи и не переписывай смысл.
# - Если есть падение/краш/500 — сначала добавь тест воспроизведения, потом фиксь до зелёного.

