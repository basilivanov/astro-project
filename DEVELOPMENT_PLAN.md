# AstroSaaS: B2C Telegram-First Pivot

## 🎯 Глобальная цель
Создать массовый B2C сервис астрологических прогнозов с доступом через Telegram Mini App и Web.
**Ключевые фичи:** Подписка (Recurrent), Реферальная система (Дни или Деньги), Виральность, Низкая себестоимость.

## 🏗 Архитектура v3.0 (Hybrid)

### 1. Telegram Centric Auth
- **Вход:** Через Telegram Widget (Web) или `initData` (Mini App).
- **Идентификатор:** `telegram_id`.
- **Профиль:** Хранит настройки, баланс, статус партнера.
- **Onboarding:** Сбор данных (Дата/Время/Место) после входа. Режим "Без времени рождения" (Космограмма).

### 2. Billing Engine
- **Провайдер:** ЮKassa (поддержка рекуррентных платежей + СБП).
- **Модель:**
  - **Подписка:** 990₽/мес (полный доступ).
  - **Разовая покупка:** 299₽ за отчет.
- **Управление:** Кнопка "Управление подпиской" в профиле.

### 3. Referral & Viral System
- **Инвайт-ссылка:** `t.me/AstroGraceBot?start=ref_USERID`.
- **Логика вознаграждения:**
  - **Для Новичка (Referee):** 15 дней Premium-доступа бесплатно сразу после регистрации (Trial).
  - **Для Пригласившего (Referrer - User):** +15 дней к текущей дате окончания подписки (сдвиг даты списания).
  - **Для Партнера (Referrer - Partner):** 20% (настраиваемо) от платежей реферала на баланс (вместо дней). Режим включается админом.
- **Вывод:** Ручной, от 1000₽, через запрос в поддержку.

### 4. LLM Optimization (Cost/Quality)
- **High-End (Claude 3.5 / GPT-4o):** Для платных глубоких отчетов.
- **Low-Cost (GPT-4o-mini / Flash):** Для ежедневных гороскопов, хораров.
- **Hybrid Mode:** Шаблонизация аспектов + персонализация вступления.

### 5. Frontend (Mobile First)
- **Лендинг:** Продающая страница -> Бот.
- **App:** PWA / SPA внутри Telegram.
- **UI:** Bottom Navigation (Сегодня, Прогнозы, Создать, Профиль).

---

## 🛠 Компоненты и Модели

### Database (New Models)
- `User`: `telegram_id`, `is_partner` (bool), `balance` (decimal), `subscription_active_until` (datetime), `birth_time_known` (bool).
- `Subscription`: `status`, `next_billing_at`, `payment_method_id` (YooKassa).
- `Referral`: Связь `referrer` -> `referee`, `reward_type` (days/money).

### Integrations
- **Telegram Bot:** Aiogram 3.x.
- **Payments:** Yookassa SDK.

---

## 📈 Roadmap

1.  **Database Layer:** Миграции Users, Billing, Referrals.
2.  **Logic:** Сервис начисления бонусов (Дни vs Деньги).
3.  **Bot:** Вход, обработка реф-ссылок.
4.  **Frontend:** UI профиля и ленты.
5.  **Billing:** Интеграция платежей.
