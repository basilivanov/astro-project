export const metadata = {
  title: "Конфиденциальность",
  description: "Политика обработки персональных данных AstroGrace",
};

export default function PrivacyPage() {
  return (
    <div className="p-6 pt-8 pb-24 max-w-2xl mx-auto text-zinc-300 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white mb-2">Политика конфиденциальности</h1>
        <p className="text-sm text-zinc-500">Редакция от 20.01.2026</p>
      </header>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">1. Сбор данных</h2>
        <p>1.1. Мы собираем следующие данные: ID пользователя Telegram, имя, данные рождения (дата, время, место) для астрологических расчетов.</p>
        <p>1.2. Данные используются исключительно для генерации персональных отчетов и не передаются третьим лицам, за исключением платежных шлюзов (для проведения оплаты).</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">2. Хранение данных</h2>
        <p>2.1. Мы принимаем все необходимые меры для защиты ваших данных от несанкционированного доступа.</p>
        <p>2.2. Вы можете в любой момент запросить удаление своих данных, обратившись в поддержку.</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">3. Использование Cookie</h2>
        <p>3.1. Сервис использует файлы cookie и локальное хранилище браузера для сохранения настроек и авторизации сессии.</p>
      </section>
    </div>
  );
}
