// ############################################################################
// AI_HEADER: MODULE_LEGAL_TERMS
// ROLE: Static page for Terms of Service.
// DEPENDENCIES: None.
// GRACE_ANCHORS: [LEGAL_TERMS]
// ############################################################################

export const metadata = {
  title: "Оферта",
  description: "Публичная оферта сервиса AstroGrace",
};

// #START_BLOCK_LEGAL_TERMS
export default function TermsPage() {
  return (
    <div className="p-6 pt-8 pb-24 max-w-2xl mx-auto text-zinc-300 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white mb-2">Публичная оферта</h1>
        <p className="text-sm text-zinc-500">Редакция от 20.01.2026</p>
      </header>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">1. Общие положения</h2>
        <p>1.1. Настоящий документ является публичной офертой сервиса AstroGrace (далее — Исполнитель) и содержит условия предоставления информационных услуг (астрологических отчетов) физическим лицам (далее — Заказчик).</p>
        <p>1.2. Оплата услуг означает полное и безоговорочное принятие условий данной оферты (акцепт).</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">2. Предмет оферты</h2>
        <p>2.1. Исполнитель обязуется предоставить Заказчику доступ к автоматизированному сервису генерации астрологических отчетов на основе предоставленных данных.</p>
        <p>2.2. Услуга считается оказанной в момент предоставления доступа к сгенерированному отчету (отображение текста в приложении или ссылка на скачивание).</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">3. Стоимость и порядок оплаты</h2>
        <p>3.1. Стоимость услуг определяется тарифами, опубликованными в интерфейсе приложения.</p>
        <p>3.2. При оформлении подписки средства списываются автоматически (рекуррентные платежи) до момента отмены подписки Заказчиком.</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">4. Политика возврата</h2>
        <p>4.1. В случае технического сбоя, препятствующего получению услуги, Заказчик вправе требовать возврата средств.</p>
        <p>4.2. Услуги надлежащего качества возврату не подлежат, так как являются нематериальным цифровым контентом.</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-bold text-white">5. Реквизиты</h2>
        <p>ИП Астролог И.И.<br/>ИНН 1234567890<br/>support@astrograce.ru</p>
      </section>
    </div>
  );
}
// #END_BLOCK_LEGAL_TERMS
