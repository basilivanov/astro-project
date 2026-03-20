# Admin UI для `natal_master`

Новый экран `frontend/app/reports/[id]/page.tsx` даёт администратору один рабочий пульт:

- sticky-панель со статусом отчёта, прогрессом и действиями `Сгенерить всё`, `Скачать Markdown`, `Скачать PDF`;
- аккордеоны по секциям `natal_master`, где первые 3 открыты сразу;
- кнопки запуска/перезапуска по секции, статус, мини-превью и безопасный fallback-показ текста;
- быстрые callout-блоки для `executive_summary` и `final_synthesis` с подсветкой fallback-маркеров;
- боковую очередь наблюдения по нескольким отчётам;
- журнал запусков внизу страницы.

UI использует существующие `/api/admin/reports/:id`, `/api/admin/reports/:id/sections/:section`, `/api/admin/reports/:id/regenerate/async` и `/api/admin/reports/:id/sections/:section/regenerate/async`.
