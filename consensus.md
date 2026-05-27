# Итоговый Consensus Council

## 1. Решение по названиям
Мы согласны с предложенными в ТЗ вариантами, так как они логичны, не конфликтуют с существующими инструментами и четко отражают суть платформы:
- **Продукт/проект:** GRACE Portable Orchestrator
- **Канонический architecture title:** Portable GRACE Orchestration Platform
- **Package/repo name:** `grace-orchestrator`

## 2. Must-fix до реализации (Архитектурные дыры и критичные ошибки)
Базируясь на архитектурном документе и статусе `EXECUTION_PACKET.md` (в котором Independent Reviewer вернул статус REWORK_REQUIRED), выявлены следующие критичные проблемы, которые **обязательно** нужно исправить до завершения MVP-2 и старта MVP-3 (или перехода к live-agent выполнению):

1. **Нестрогая фильтрация (Portability / Runtime boundary risk):**
   Обнаружено, что backlog controller использует `lenient` режим парсинга и подхватывает старые артефакты, evidence-файлы и роли (legacy role packets), если в них случайно оказываются поля с ID. Это критический риск, так как оркестратор будет пытаться выполнить не-runnable файлы. **Решение:** Требуется использовать только strict-валидацию по умолчанию. У файлов без строгих контрактов (`Allowed Write Scope`, `Verification` и т.д.) не должно быть статуса runnable.

2. **Отсутствие контрактов в коде (Operational / Maintenance risk):**
   Independent reviewer обнаружил, что публичные функции, например `update_dependent_packets` в `backlog_controller.py`, не имеют обязательного `START_FUNCTION_CONTRACT`. Это нарушает "GRACE Canon Script Discipline". **Решение:** Строго следовать собственному контракту написания кода во всех новых публичных функциях.

3. **Смешение состояний (Contract / Runtime boundary risk):**
   `passed` - это сигнал от локального гейта, он не должен автоматически приравниваться к `accepted` или становиться терминальным статусом в `RegistryStatus`. Если это не исправить, возможны ложноположительные завершения конвейера. Валидатор DAG должен оперировать только strict статусами registry, а не domain statuses.

4. **Риск потери контекста блокировки при каскадировании:**
   В текущем варианте `submit-packets` и `sync-packets` (из-за недавних фиксов это стало лучше, но риск остается на уровне DAG) зависимые от заблокированного пакета должны помечаться именно как `cascading_blocked`, а не просто `blocked`.

5. **Изоляция исполнения (Install boundary risk):**
   Архитектурный документ упоминает `worktree_strategy`. До тех пор, пока `WorktreeManager` не внедрен полностью, запрещен любой запуск реальных агентов (`--execute-agent`). Попытка submit без worktree isolation может повредить основной репозиторий. Команда `submit-packets --execute` должна fail-closed (что, судя по ревью, сейчас работает с `SAFETY_GATE_NOT_READY`, но требует сохранения этого поведения как инварианта).

## 3. Should-fix для MVP (Недорогие улучшения без раздувания scope)
1. **Четкая диаграмма состояний (State Machine Diagram):**
   В ТЗ описаны слои статусов (SourcePacketStatus, RegistryStatus, DomainStatus). Для переносимости крайне важно добавить краткую Mermaid-диаграмму переходов статусов в `docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`.
2. **Failure-mode matrix:**
   Как описано в задаче (failure-mode matrix), добавить таблицу, показывающую, как система деградирует (например, недоступен Prefect -> локальный `DryRunRuntime`, недоступен Docker -> запуск в `project_venv`, недоступен Codex -> fallback на `agy`). Это не требует кода, но прояснит contract.
3. **Улучшение UX сухого прогона (Dry-Run):**
   Команда `submit-packets --json` в пустом registry сообщает `ok: true`, что запутывает оператора (пользователь думает, что всё отправлено, хотя очередь пуста). Следует возвращать предупреждение/сообщение о пустом registry и предлагать запустить `sync-packets`.

## 4. Вердикт
**NO-GO (REWORK_REQUIRED)** для текущей имплементации пакета `FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER`.
Хотя часть архитектуры выглядит солидно, наличие legacy-парсинга, нарушающего строгую фильтрацию файлов, и отсутствие контрактов в коде требуют исправления (rework) до того, как этот слой станет фундаментом для Portable GRACE. Архитектурный план (PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md) в целом жизнеспособен, но нуждается в ужесточении фильтрации исходных пакетов.